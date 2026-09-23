import os
import sqlite3
from contextlib import closing
from pathlib import Path
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Literal
from fastapi import APIRouter, Header, Query, HTTPException
from pydantic import BaseModel, Field
from auth import get_token_user
from admin_users import require_admin
from database import get_connection

router = APIRouter(tags=['意见反馈'])
DB_PATH = Path(os.getenv('FEEDBACK_DB_PATH', str(Path(__file__).with_name('feedback.sqlite3'))))

def connect():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute('''CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        username TEXT NOT NULL, category TEXT NOT NULL, content TEXT NOT NULL,
        contact TEXT NOT NULL, created_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending', request_id TEXT NOT NULL,
        UNIQUE(user_id, request_id))''')
    columns = {r[1] for r in conn.execute('PRAGMA table_info(feedback)')}
    for name in ('reply', 'replied_at'):
        if name not in columns: conn.execute(f"ALTER TABLE feedback ADD COLUMN {name} TEXT NOT NULL DEFAULT ''")
    conn.commit()
    return conn

class FeedbackRequest(BaseModel):
    category: Literal['功能建议', '数据问题', '页面问题', '其他']
    content: str = Field(min_length=5, max_length=2000)
    contact: str = Field(default='', max_length=120)
    request_id: UUID

@router.post('/feedback')
def submit_feedback(data: FeedbackRequest, authorization: str = Header(default=None)):
    user_id = get_token_user(authorization)
    content = data.content.strip()
    if len(content) < 5: raise HTTPException(status_code=400, detail='请至少填写5个字的反馈内容')
    with closing(get_connection()) as db:
        cursor = db.cursor()
        cursor.execute('SELECT username FROM sys_user WHERE id = ?', user_id)
        user = cursor.fetchone()
        if not user: raise HTTPException(status_code=401, detail='账号不存在')
        username = user.username
    with closing(connect()) as conn:
        conn.execute('''INSERT OR IGNORE INTO feedback
            (user_id,username,category,content,contact,created_at,request_id) VALUES (?,?,?,?,?,?,?)''',
            (user_id, username, data.category, content, data.contact.strip(),
             datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'), str(data.request_id)))
        conn.commit()
        row = conn.execute('SELECT id FROM feedback WHERE user_id=? AND request_id=?', (user_id, str(data.request_id))).fetchone()
        return {'id': row['id'], 'message': '反馈已提交，感谢你的建议'}

def list_records(user_id, page):
    where, params = (' WHERE user_id=?', [user_id]) if user_id is not None else ('', [])
    with closing(connect()) as conn:
        total = conn.execute('SELECT COUNT(*) FROM feedback' + where, params).fetchone()[0]
        rows = conn.execute('SELECT id,user_id,username,category,content,contact,created_at,status,reply,replied_at FROM feedback' + where + ' ORDER BY id DESC LIMIT 20 OFFSET ?', params + [(page-1)*20]).fetchall()
        return {'items': [dict(row) for row in rows], 'total': total}

@router.get('/feedback')
def my_feedback(authorization: str = Header(default=None), page: int = Query(default=1, ge=1)):
    return list_records(get_token_user(authorization), page)

@router.get('/admin/feedback')
def all_feedback(authorization: str = Header(default=None), page: int = Query(default=1, ge=1)):
    require_admin(authorization)
    return list_records(None, page)

class FeedbackStatus(BaseModel):
    status: Literal['pending', 'handled']
    reply: str | None = Field(default=None, max_length=2000)

@router.put('/admin/feedback/{feedback_id}')
def update_feedback(feedback_id: int, data: FeedbackStatus, authorization: str = Header(default=None)):
    require_admin(authorization)
    with closing(connect()) as conn:
        count = conn.execute('UPDATE feedback SET status=? WHERE id=?', (data.status, feedback_id)).rowcount
        if not count: raise HTTPException(status_code=404, detail='反馈不存在')
        if data.reply is not None:
            conn.execute('UPDATE feedback SET reply=?,replied_at=? WHERE id=?',
                         (data.reply.strip(), datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'), feedback_id))
        conn.commit()
    return {'status': data.status, 'reply': data.reply}
