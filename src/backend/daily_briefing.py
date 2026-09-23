"""Durable per-account inbox and daily delivery claims (Beijing time)."""
import logging
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from database import get_connection
from forecast_service import get_7d_forecast
from email_service import send_briefing_email

DB_PATH = Path(os.getenv('BRIEFING_DB_PATH', str(Path(__file__).with_name('daily_briefings.sqlite3'))))
CHINA = timezone(timedelta(hours=8))
logger = logging.getLogger(__name__)

def connect():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('''CREATE TABLE IF NOT EXISTS briefings (
        user_id INTEGER NOT NULL, day TEXT NOT NULL, title TEXT, content TEXT,
        created_at TEXT, read INTEGER NOT NULL DEFAULT 0,
        email_status TEXT NOT NULL DEFAULT 'pending', PRIMARY KEY(user_id, day))''')
    if 'email_error' not in {r[1] for r in conn.execute('PRAGMA table_info(briefings)')}:
        conn.execute("ALTER TABLE briefings ADD COLUMN email_error TEXT NOT NULL DEFAULT ''")
    conn.commit()
    return conn

def profile(user_id):
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT last_lat, last_lng, last_address, email, push_enable
                          FROM sys_user WHERE id = ? AND status = 1''', user_id)
        return cursor.fetchone()

def weather_text(code):
    if code == 0: return '晴'
    if code in (1, 2, 3): return '晴间多云或阴'
    if code in (45, 48): return '雾'
    if code in (51, 53, 55, 56, 57): return '毛毛雨'
    if code in (61, 63, 65, 66, 67, 80, 81, 82): return '有雨'
    if code in (71, 73, 75, 77, 85, 86): return '有雪'
    if code in (95, 96, 99): return '雷雨'
    return '天气状况暂无数据'

def compose(day, address, forecast):
    today = next((item for item in forecast if item.get('date') == day), None)
    if today is None: raise ValueError('缺少当日预报，稍后重试')
    def value(key, unit):
        v = today.get(key)
        return '暂无数据' if v is None else f'{v}{unit}'
    tips = []
    if (today.get('precipitation_probability') or 0) >= 50: tips.append('降雨概率较高，出门记得带伞。')
    if today.get('temperature_max') is not None and today['temperature_max'] >= 32: tips.append('白天气温较高，注意防晒补水。')
    if today.get('temperature_min') is not None and today['temperature_min'] <= 5: tips.append('早晚较冷，注意添衣保暖。')
    if (today.get('wind_speed_max') or 0) >= 40: tips.append('风速较大，外出留意高空坠物。')
    return '\n'.join([
        f'{day} · 每日天气早报', f'所在地：{address}',
        f'今日天气：{weather_text(today.get("weather_code"))}',
        f'气温：{value("temperature_min", "℃")} ～ {value("temperature_max", "℃")}',
        f'最高降雨概率：{value("precipitation_probability", "%")}',
        f'预计降水量：{value("precipitation_sum", " mm")}',
        f'最大风速：{value("wind_speed_max", " km/h")}', '',
        '出行提示：' + (' '.join(tips) or '请根据气温安排穿着，出行前留意最新天气。'), '',
        '数据来源：Open-Meteo，按已保存位置生成；预报可能更新，请以最新预报为准。'])

def ensure_daily_briefing(user_id):
    """Never break login. Claim email atomically; do not retry ambiguous SMTP sends."""
    try:
        user = profile(user_id)
        if not user or user.last_lat is None or user.last_lng is None: return
        now = datetime.now(CHINA)
        day = now.date().isoformat()
        with closing(connect()) as conn:
            row = conn.execute('SELECT * FROM briefings WHERE user_id=? AND day=?', (user_id, day)).fetchone()
            if row is None:
                lat, lng = float(user.last_lat), float(user.last_lng)
                if not (-90 <= lat <= 90 and -180 <= lng <= 180): return
                address = user.last_address or f'{lat:.4f}°N, {lng:.4f}°E'
                content = compose(day, address, get_7d_forecast(lat, lng))
                conn.execute('''INSERT OR IGNORE INTO briefings
                    (user_id, day, title, content, created_at) VALUES (?, ?, ?, ?, ?)''',
                    (user_id, day, f'每日天气早报 · {day}', content, now.strftime('%Y-%m-%d %H:%M')))
                conn.commit()
            if not user.email or user.push_enable == 0:
                conn.execute("UPDATE briefings SET email_status=? WHERE user_id=? AND day=? AND email_status IN ('pending','no_email','disabled')",
                             ('no_email' if not user.email else 'disabled', user_id, day))
                conn.commit()
                return
            claimed = conn.execute("UPDATE briefings SET email_status='sending' WHERE user_id=? AND day=? AND email_status IN ('pending','no_email','disabled')", (user_id, day)).rowcount
            conn.commit()
            if not claimed: return
            row = conn.execute('SELECT * FROM briefings WHERE user_id=? AND day=?', (user_id, day)).fetchone()
            try:
                send_briefing_email(user.email, row['title'], row['content'])
                status = 'sent'
            except Exception:
                logger.exception('Daily briefing email failed for account %s', user_id)
                status = 'failed'
            conn.execute('UPDATE briefings SET email_status=? WHERE user_id=? AND day=?', (status, user_id, day))
            conn.commit()
    except Exception:
        logger.exception('Daily briefing generation failed for account %s', user_id)

def inbox(user_id):
    with closing(connect()) as conn:
        rows = conn.execute('SELECT * FROM briefings WHERE user_id=? ORDER BY day DESC LIMIT 30', (user_id,)).fetchall()
        return [dict(id=f'briefing:{row["day"]}', title=row['title'], description=row['content'],
                     publish_time=row['created_at'], read=bool(row['read']), email_status=row['email_status'],
                     email_error=row['email_error'], kind=('晚间天气报告' if row['day'].endswith(':evening') else
                         '午间天气报告' if row['day'].endswith(':noon') else '早间天气报告')) for row in rows]

def mark_read(user_id, ids):
    with closing(connect()) as conn:
        conn.executemany('UPDATE briefings SET read=1 WHERE user_id=? AND day=?',
                         [(user_id, item.removeprefix('briefing:')) for item in ids if item.startswith('briefing:')])
        conn.commit()
