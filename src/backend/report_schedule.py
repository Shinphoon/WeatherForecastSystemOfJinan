"""Durable morning/noon/evening report schedules, Beijing time."""
import logging
import re
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
import daily_briefing as b

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/auth')

def connect():
    conn=b.connect()
    conn.execute('''CREATE TABLE IF NOT EXISTS report_schedule (
        user_id INTEGER PRIMARY KEY, morning TEXT NOT NULL DEFAULT '07:00', evening TEXT NOT NULL DEFAULT '18:00')''')
    columns = {row[1] for row in conn.execute('PRAGMA table_info(report_schedule)')}
    for name, definition in {
        'noon': "TEXT NOT NULL DEFAULT '15:20'",
        'morning_enabled': 'INTEGER NOT NULL DEFAULT 1',
        'noon_enabled': 'INTEGER NOT NULL DEFAULT 1',
        'evening_enabled': 'INTEGER NOT NULL DEFAULT 1',
    }.items():
        if name not in columns:
            conn.execute(f'ALTER TABLE report_schedule ADD COLUMN {name} {definition}')
    conn.commit()
    return conn

def schedule(user_id):
    with closing(connect()) as conn:
        row=conn.execute('''SELECT morning,noon,evening,morning_enabled,noon_enabled,evening_enabled
                            FROM report_schedule WHERE user_id=?''',(user_id,)).fetchone()
        return dict(row) if row else {'morning':'07:00','noon':'15:20','evening':'18:00',
            'morning_enabled':1,'noon_enabled':1,'evening_enabled':1}

class ScheduleRequest(BaseModel):
    morning: str
    noon: str
    evening: str
    morning_enabled: bool = True
    noon_enabled: bool = True
    evening_enabled: bool = True

def validate(data):
    for value,low,high in [(data.morning,'05:00','11:00'),(data.noon,'11:00','16:30'),
                           (data.evening,'16:30','22:30')]:
        if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',value) or not low <= value <= high:
            raise HTTPException(400,'早间须在05:00—11:00，午间须在11:00—16:30，晚间须在16:30—22:30（北京时间）')

@router.get('/report-schedule')
def get_schedule(authorization: str = Header(default=None)):
    from auth import get_token_user
    return schedule(get_token_user(authorization))

@router.put('/report-schedule')
def save_schedule(data: ScheduleRequest, authorization: str = Header(default=None)):
    from auth import get_token_user
    user_id=get_token_user(authorization)
    validate(data)
    with closing(connect()) as conn:
        conn.execute('''INSERT INTO report_schedule
            (user_id,morning,noon,evening,morning_enabled,noon_enabled,evening_enabled)
            VALUES(?,?,?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET
            morning=excluded.morning,noon=excluded.noon,evening=excluded.evening,
            morning_enabled=excluded.morning_enabled,noon_enabled=excluded.noon_enabled,
            evening_enabled=excluded.evening_enabled''',
            (user_id,data.morning,data.noon,data.evening,int(data.morning_enabled),
             int(data.noon_enabled),int(data.evening_enabled)))
        conn.commit()
    return schedule(user_id)

def ensure_reports(user_id, now=None):
    try:
        now=now or datetime.now(b.CHINA)
        preferences=schedule(user_id)
        for kind,cutoff in [('morning','11:00'),('noon','16:30'),('evening','22:30')]:
            current=now.strftime('%H:%M')
            if not preferences[f'{kind}_enabled'] or not preferences[kind] <= current <= cutoff: continue
            key=now.date().isoformat()+':'+kind
            with closing(connect()) as conn:
                if conn.execute('SELECT 1 FROM briefings WHERE user_id=? AND day=?',(user_id,key)).fetchone(): continue
            user=b.profile(user_id)
            if not user or user.last_lat is None or user.last_lng is None: continue
            lat,lng=float(user.last_lat),float(user.last_lng)
            if not (-90<=lat<=90 and -180<=lng<=180): continue
            label={'morning':'早间天气报告','noon':'午间天气报告','evening':'晚间天气报告'}[kind]
            target=(now+timedelta(days=1)).date() if kind=='evening' else now.date()
            content=b.compose(target.isoformat(),user.last_address or '已保存的位置',b.get_7d_forecast(lat,lng))
            content=content.replace('每日天气早报',label)
            if kind=='evening': content=content.replace('今日天气','明日天气')
            title=label+' · '+now.date().isoformat()
            status='sending' if user.email and user.push_enable != 0 else ('no_email' if not user.email else 'disabled')
            with closing(connect()) as conn:
                inserted=conn.execute('INSERT OR IGNORE INTO briefings(user_id,day,title,content,created_at,email_status) VALUES(?,?,?,?,?,?)',
                    (user_id,key,title,content,now.strftime('%Y-%m-%d %H:%M'),status)).rowcount
                conn.commit()
            if not inserted or status!='sending': continue
            error=''
            try:
                b.send_briefing_email(user.email,title,content)
                status='sent'
            except Exception as exc:
                from email_service import delivery_error
                status='failed';error=delivery_error(exc)
                logger.exception('Scheduled report email failed for account %s',user_id)
            with closing(connect()) as conn:
                conn.execute('UPDATE briefings SET email_status=?,email_error=? WHERE user_id=? AND day=?',(status,error,user_id,key))
                conn.commit()
    except Exception:
        logger.exception('Scheduled report failed for account %s',user_id)

def check_all_reports():
    with closing(b.get_connection()) as conn:
        cursor=conn.cursor()
        cursor.execute('SELECT id FROM sys_user WHERE status=1 AND last_lat IS NOT NULL AND last_lng IS NOT NULL')
        ids=[row.id for row in cursor.fetchall()]
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(ensure_reports,ids))
