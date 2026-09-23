import requests
from bs4 import BeautifulSoup
from functools import lru_cache


STATION_NAMES = {
    "54727": "章丘",
    "54816": "长清",
    "54818": "平阴",
    "54821": "济阳",
    "54823": "济南",
    "54828": "莱芜"
}


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/152.0.0.0 Safari/537.36"
    )
}


def get_station_name(station_id):

    return STATION_NAMES.get(
        station_id,
        station_id
    )


# ==============================
# 获取站点基本信息
# 纬度、经度、海拔
# ==============================

@lru_cache(maxsize=32)
def get_station_info(station_id):

    url = (
        f"https://q-weather.info/"
        f"api/weather/{station_id}/"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()


    return {
        "station": station_id,
        "name": get_station_name(station_id),
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "alt": data.get("alt")
    }


# ==============================
# 当前实况
# ==============================

from observation_parser import parse_realtime, parse_hourly


def get_realtime_weather(station_id):
    response = requests.get(f'https://q-weather.info/weather/{station_id}/realtime/', headers=HEADERS, timeout=10)
    response.raise_for_status()
    return {**parse_realtime(response.text, station_id), 'city': get_station_name(station_id)}


def get_today_weather(station_id):
    response = requests.get(f'https://q-weather.info/weather/{station_id}/today/', headers=HEADERS, timeout=10)
    response.raise_for_status()
    return parse_hourly(response.text)


@lru_cache(maxsize=512)
def get_history_weather(station_id, date):
    response = requests.get(f'https://q-weather.info/weather/{station_id}/history/', params={'date': date}, headers=HEADERS, timeout=10)
    response.raise_for_status()
    result = parse_hourly(response.text)
    if not result: raise ValueError('历史观测暂不可用')
    return result
