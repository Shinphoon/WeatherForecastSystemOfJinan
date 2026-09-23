from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel
from typing import Literal
from database import get_connection
from auth import get_token_user

router = APIRouter(prefix='/admin', tags=['用户管理'])


def require_admin(authorization):
    user_id = get_token_user(authorization)
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT role, status FROM sys_user WHERE id = ?', user_id)
        user = cursor.fetchone()
        if not user or user.role != 'admin' or user.status != 1:
            raise HTTPException(status_code=403, detail='仅已启用的管理员可管理用户')
        return user_id
    finally:
        conn.close()


@router.get('/users')
def list_users(authorization: str = Header(default=None), page: int = Query(default=1, ge=1),
               page_size: int = Query(default=20, ge=1, le=100)):
    viewer_id = require_admin(authorization)
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM sys_user')
        total = cursor.fetchone()[0]
        cursor.execute('''SELECT id, username, nickname, phone, email, role, status,
            push_enable, last_address, last_lat, last_lng, create_time, update_time
            FROM sys_user ORDER BY id OFFSET ? ROWS FETCH NEXT ? ROWS ONLY''',
            (page - 1) * page_size, page_size)
        columns = [column[0] for column in cursor.description]
        users = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return {'users': users, 'total': total, 'page': page, 'page_size': page_size, 'viewer_id': viewer_id}
    finally:
        conn.close()


class UserStatusRequest(BaseModel):
    status: Literal[0, 1]


@router.put('/users/{user_id}/status')
def set_user_status(user_id: int, data: UserStatusRequest, authorization: str = Header(default=None)):
    admin_id = require_admin(authorization)
    if user_id == admin_id:
        raise HTTPException(status_code=400, detail='不能封禁或修改自己的账号状态')
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM sys_user WITH (UPDLOCK, HOLDLOCK) WHERE id = ?', user_id)
        target = cursor.fetchone()
        if not target:
            raise HTTPException(status_code=404, detail='用户不存在')
        if target.role == 'admin':
            raise HTTPException(status_code=400, detail='管理员账号不支持在此封禁')
        cursor.execute('UPDATE sys_user SET status = ?, update_time = GETDATE() WHERE id = ?', data.status, user_id)
        conn.commit()
        return {'id': user_id, 'status': data.status, 'message': '账号已封禁' if data.status == 0 else '账号已解封'}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
