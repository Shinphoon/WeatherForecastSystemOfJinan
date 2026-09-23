"""Account-scoped approaching-rain notifications, shared by login and periodic checks."""
import logging
import math
import time
import uuid
from contextlib import closing
from datetime import datetime

import daily_briefing as storage
from radar_alert_service import get_radar_approach
from email_service import send_briefing_email, delivery_error

logger = logging.getLogger(__name__)


def connect():
    conn = storage.connect()
    conn.execute('''CREATE TABLE IF NOT EXISTS rain_notifications (
        id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, created REAL NOT NULL,
        content TEXT NOT NULL, read INTEGER NOT NULL DEFAULT 0,
        email_status TEXT NOT NULL)''')
    conn.execute('CREATE INDEX IF NOT EXISTS rain_user_time ON rain_notifications(user_id, created)')
    conn.execute('''CREATE TABLE IF NOT EXISTS rain_checks (
        user_id INTEGER PRIMARY KEY, checked REAL NOT NULL)''')
    if 'email_error' not in {r[1] for r in conn.execute('PRAGMA table_info(rain_notifications)')}:
        conn.execute("ALTER TABLE rain_notifications ADD COLUMN email_error TEXT NOT NULL DEFAULT ''")
    conn.commit()
    return conn


def eligible(result, now):
    eta = result.get('eta_minutes')
    frames = result.get('frames') or []
    return (result.get('status') == 'approaching'
            and isinstance(eta, (int, float)) and math.isfinite(eta) and 0 < eta <= 60
            and len(frames) >= 3
            and all(isinstance(f.get('time'), (int, float)) and 0 <= now - f['time'] <= 1800 for f in frames)
            and frames[-1].get('distance_km') is not None
            and frames[-1]['distance_km'] > 2)


def check_rain(user_id):
    """No network work inside DB transactions; atomically claim checks and delivery."""
    try:
        user = storage.profile(user_id)
        if not user or user.last_lat is None or user.last_lng is None:
            return
        lat, lng = float(user.last_lat), float(user.last_lng)
        if not (-85 < lat < 85 and -180 <= lng <= 180):
            return
        now = time.time()
        with closing(connect()) as conn:
            claimed = conn.execute('''INSERT INTO rain_checks VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET checked=excluded.checked
                WHERE rain_checks.checked <= ?''', (user_id, now, now - 300)).rowcount
            conn.commit()
        if not claimed:
            return
        result = get_radar_approach(lat, lng)
        now = time.time()
        if not eligible(result, now):
            return
        content = (f'您所在的位置即将出现降雨，请及时携带雨具。\n'
                   f'位置：{user.last_address or "已保存的位置"}\n'
                   f'预计约 {result["eta_minutes"]} 分钟后受到降雨影响。\n'
                   '依据最近雷达回波移动趋势估算，实际降雨时间可能变化。')
        status = 'sending' if user.email and user.push_enable != 0 else ('no_email' if not user.email else 'disabled')
        notification_id = str(uuid.uuid4())
        with closing(connect()) as conn:
            conn.execute('BEGIN IMMEDIATE')
            recent = conn.execute('SELECT 1 FROM rain_notifications WHERE user_id=? AND created>?',
                                  (user_id, now - 3600)).fetchone()
            if recent:
                return
            conn.execute('INSERT INTO rain_notifications(id,user_id,created,content,email_status) VALUES(?,?,?,?,?)',
                         (notification_id, user_id, now, content, status))
            conn.commit()
        if status == 'sending':
            error = ''
            try:
                send_briefing_email(user.email, '降雨提醒：您所在的位置即将出现降雨', content)
                status = 'sent'
            except Exception as exc:
                error = delivery_error(exc)
                logger.exception('Rain email failed for account %s', user_id)
                status = 'failed'
            with closing(connect()) as conn:
                conn.execute('UPDATE rain_notifications SET email_status=?,email_error=? WHERE id=?', (status, error, notification_id))
                conn.commit()
    except Exception:
        logger.exception('Rain check skipped for account %s', user_id)


def inbox(user_id):
    with closing(connect()) as conn:
        rows = conn.execute('SELECT * FROM rain_notifications WHERE user_id=? ORDER BY created DESC LIMIT 30', (user_id,)).fetchall()
        return [dict(id='rain:' + r['id'], title='您所在的位置即将出现降雨',
                     description=r['content'], kind='临近降雨提醒', read=bool(r['read']),
                     email_status=r['email_status'], email_error=r['email_error'],
                     publish_time=datetime.fromtimestamp(r['created'], storage.CHINA).strftime('%Y-%m-%d %H:%M')) for r in rows]


def mark_read(user_id, ids):
    with closing(connect()) as conn:
        conn.executemany('UPDATE rain_notifications SET read=1 WHERE user_id=? AND id=?',
                         [(user_id, i[5:]) for i in ids if i.startswith('rain:')])
        conn.commit()
