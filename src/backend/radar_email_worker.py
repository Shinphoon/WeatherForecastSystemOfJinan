from datetime import datetime, timedelta

from database import get_connection
from radar_alert_service import get_radar_approach
from email_service import send_radar_email


# ETA 60分钟以内才发送
ETA_THRESHOLD_MINUTES = 60

# 相同类型邮件至少间隔60分钟
COOLDOWN_MINUTES = 60


def can_send_email(
    cursor,
    user_id,
    radar_status
):
    cursor.execute(
        """
        SELECT TOP 1
            status,
            sent_time
        FROM dbo.radar_email_log
        WHERE user_id = ?
        ORDER BY sent_time DESC
        """,
        user_id
    )

    row = cursor.fetchone()

    # 从没发过
    if not row:
        return True

    # 状态变了，例如 approaching → raining
    # 可以立即再发一封
    if row.status != radar_status:
        return True

    # 相同状态检查冷却时间
    if row.sent_time:
        delta = (
            datetime.now()
            - row.sent_time
        )

        if delta < timedelta(
            minutes=COOLDOWN_MINUTES
        ):
            return False

    return True


def save_email_log(
    user_id,
    status,
    distance_km,
    eta_minutes
):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO dbo.radar_email_log
            (
                user_id,
                status,
                distance_km,
                eta_minutes
            )
            VALUES (?, ?, ?, ?)
            """,
            user_id,
            status,
            distance_km,
            eta_minutes
        )

        conn.commit()

    finally:
        cursor.close()
        conn.close()


def check_one_user(user):
    from rain_notifications import check_rain
    check_rain(user.id)


def check_all_users():
    print(
        "[雷达邮件] 开始自动检查用户..."
    )

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                id,
                email,
                push_enable,
                last_lat,
                last_lng,
                last_address
            FROM dbo.sys_user
            WHERE status = 1
              AND last_lat IS NOT NULL
              AND last_lng IS NOT NULL
            """
        )

        users = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    print(
        f"[雷达邮件] 共检查 {len(users)} 个用户"
    )

    for user in users:
        check_one_user(user)

    print(
        "[雷达邮件] 本轮检查结束"
    )