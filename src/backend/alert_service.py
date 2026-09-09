import requests
from bs4 import BeautifulSoup
from datetime import datetime

MOCK_ALERT = None

LIST_URL = "https://e.weather.com.cn/alarmMap/list.html"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/152.0.0.0 Safari/537.36"
    )
}

JINAN_KEYWORDS = [
    "济南",
    "历下",
    "市中",
    "槐荫",
    "天桥",
    "历城",
    "长清",
    "章丘",
    "济阳",
    "莱芜",
    "钢城",
    "平阴",
    "商河"
]

def is_jinan_alert(text: str):
    return any(keyword in text for keyword in JINAN_KEYWORDS)

def parse_level(title: str):
    for level in ["红色", "橙色", "黄色", "蓝色"]:
        if level in title:
            return level
    return ""

def parse_type(title: str):
    types = [
        "暴雨", "雷电", "大风", "高温", "暴雪",
        "寒潮", "大雾", "冰雹", "道路结冰",
        "霾", "沙尘暴", "台风", "霜冻"
    ]
    for alert_type in types:
        if alert_type in title:
            return alert_type
    return "其他"

def get_jinan_alerts():
    response = requests.get(
        LIST_URL,
        headers=HEADERS,
        timeout=10
    )
    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    alerts = []

    for link in soup.find_all("a"):
        title = link.get_text(
            " ",
            strip=True
        )

        href = link.get("href")

        if not title or not href:
            continue

        if not is_jinan_alert(title):
            continue

        if "预警" not in title:
            continue

        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = "https://e.weather.com.cn" + href

        alerts.append({
            "title": title,
            "type": parse_type(title),
            "level": parse_level(title),
            "url": href
        })

    unique = []
    seen = set()

    for alert in alerts:
        key = alert["title"]

        if key not in seen:
            seen.add(key)
            unique.append(alert)

    return unique

def get_current_alert_summary():
    if MOCK_ALERT:
        return {
            "has_alert": True,
            "count": 1,
            "latest": MOCK_ALERT,
            "alerts": [MOCK_ALERT],
            "update_time": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "mock": True
        }

    alerts = get_jinan_alerts()

    if not alerts:
        return {
            "has_alert": False,
            "count": 0,
            "latest": None,
            "update_time":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
        }

    return {
        "has_alert": True,
        "count": len(alerts),
        "latest": alerts[0],
        "alerts": alerts,
        "update_time":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
    }

def set_mock_alert(alert):
    global MOCK_ALERT
    MOCK_ALERT = alert

def clear_mock_alert():
    global MOCK_ALERT
    MOCK_ALERT = None