import os
import smtplib
import ssl

from pathlib import Path
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr


# 项目根目录：
# D:\WebGIS实习\jinan-weather
BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
)

ENV_PATH = BASE_DIR / ".env"

load_dotenv(
    ENV_PATH,
    override=True
)


def send_briefing_email(to_email, subject, content):
    sender = os.getenv('GMAIL_SENDER_EMAIL') or os.getenv('SMTP_SENDER_EMAIL', '')
    password = os.getenv('GMAIL_APP_PASSWORD') or os.getenv('SMTP_PASSWORD', '')
    if not sender or not password:
        raise RuntimeError('未配置发件邮箱或 SMTP 授权码')
    host = 'smtp.gmail.com' if os.getenv('GMAIL_SENDER_EMAIL') else os.getenv('SMTP_HOST', 'smtp.gmail.com')
    port = 465 if os.getenv('GMAIL_SENDER_EMAIL') else int(os.getenv('SMTP_PORT', '587'))
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = formataddr((str(Header('济南天气', 'utf-8')), sender))
    message['To'] = to_email
    message['Subject'] = Header(subject, 'utf-8')
    server = (smtplib.SMTP_SSL(host, port, timeout=20, context=ssl.create_default_context())
              if port == 465 else smtplib.SMTP(host, port, timeout=20))
    with server:
        if port != 465: server.starttls(context=ssl.create_default_context())
        server.login(sender, password.replace(' ', ''))
        server.send_message(message)


def send_radar_email(
    to_email,
    status,
    distance_km=None,
    eta_minutes=None,
    address=None
):
    sender_email = os.getenv(
        "GMAIL_SENDER_EMAIL",
        ""
    ).strip()

    app_password = os.getenv(
        "GMAIL_APP_PASSWORD",
        ""
    ).replace(" ", "").strip()

    if not sender_email:
        raise RuntimeError(
            "未配置 GMAIL_SENDER_EMAIL"
        )

    if not app_password:
        raise RuntimeError(
            "未配置 GMAIL_APP_PASSWORD"
        )

    if not to_email:
        raise RuntimeError(
            "收件人邮箱为空"
        )

    if status == "raining":
        subject = (
            "【济南天气】"
            "当前位置附近已检测到降水回波"
        )

        content = f"""
您好：

雷达监测显示，您当前所在位置已经进入降水回波影响范围。

当前位置：
{address or "已保存的位置"}

最近降水回波距离：
{distance_km if distance_km is not None else "--"} km

建议您及时关注天气变化，外出时携带雨具。

说明：
本信息由系统根据雷达回波自动识别生成，
并非气象部门发布的官方预警。

—— 济南市天气实况与预报可视化系统
"""

    else:
        subject = (
            f"【济南天气】预计约"
            f"{eta_minutes}分钟后可能出现降雨"
        )

        content = f"""
您好：

雷达监测显示，有降水回波正在接近您所在位置。

当前位置：
{address or "已保存的位置"}

当前最近回波距离：
{distance_km if distance_km is not None else "--"} km

根据近期雷达回波移动趋势，
预计约 {eta_minutes} 分钟后可能出现降雨。

建议您提前做好出行准备。

说明：
该时间为雷达回波自动外推估计，
存在一定误差，并非气象部门发布的官方预警。

—— 济南市天气实况与预报可视化系统
"""

    send_briefing_email(to_email, subject, content.strip())
    return True

def delivery_error(exc):
    if isinstance(exc, smtplib.SMTPAuthenticationError): return '发件邮箱认证失败，请检查Gmail应用专用密码'
    if isinstance(exc, smtplib.SMTPRecipientsRefused): return '收件地址被邮件服务器拒绝，请检查邮箱地址'
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)): return '连接邮件服务器超时或失败，请检查服务器网络'
    if isinstance(exc, smtplib.SMTPException): return '邮件服务器拒绝请求或连接中断，请联系管理员检查投递日志'
    if isinstance(exc, RuntimeError): return '发件邮箱或SMTP授权码未配置'
    return '邮件发送失败，请联系管理员检查投递日志'
