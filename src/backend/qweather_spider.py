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

def get_realtime_weather(station_id):

    url = (
        f"https://q-weather.info/"
        f"weather/{station_id}/realtime/"
    )


    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )

    response.raise_for_status()


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    table = soup.find("table")


    if table is None:

        return {
            "error": "没有找到实时天气表格"
        }


    weather = {}


    rows = table.find_all("tr")


    for row in rows:

        cells = row.find_all(
            ["td", "th"]
        )


        if len(cells) < 2:
            continue


        name = cells[0].get_text(
            strip=True
        )

        value = cells[1].get_text(
            strip=True
        )


        weather[name] = value


    # 能见度不同站可能名称不完全一样
    visibility = (
        weather.get("10分钟平均能见度")
        or weather.get("能见度")
        or weather.get("报告能见度")
    )


    # 风向
    wind_direction = (
        weather.get("2分钟平均风向")
        or weather.get("瞬时风向")
    )


    # 风速
    wind_speed = (
        weather.get("2分钟平均风速")
        or weather.get("瞬时风速")
    )


    return {

        "station": station_id,

        "city": get_station_name(
            station_id
        ),

        "temperature":
            weather.get("瞬时温度"),

        "pressure":
            weather.get("地面气压"),

        "humidity":
            weather.get("相对湿度"),

        "wind_direction":
            wind_direction,

        "wind_speed":
            wind_speed,

        "rain_1h":
            weather.get("1小时降水"),

        "rain_24h":
            weather.get("24小时降水"),

        "visibility":
            visibility
    }


# ==============================
# 过去24小时实况
# ==============================

def get_today_weather(station_id):

    url = (
        f"https://q-weather.info/"
        f"weather/{station_id}/today/"
    )


    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )


    response.raise_for_status()


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    table = soup.find("table")


    if table is None:

        return {
            "error":
                "没有找到24小时天气表格"
        }


    result = []


    rows = table.find_all("tr")


    for row in rows[1:]:

        cells = row.find_all("td")


        if len(cells) < 9:
            continue


        result.append({

            "time":
                cells[0].get_text(
                    strip=True
                ),

            "temperature":
                cells[1].get_text(
                    strip=True
                ),

            "pressure":
                cells[2].get_text(
                    strip=True
                ),

            "humidity":
                cells[3].get_text(
                    strip=True
                ),

            "wind_direction":
                cells[4].get_text(
                    strip=True
                ),

            "wind_speed":
                cells[5].get_text(
                    strip=True
                ),

            "max_wind_speed_1h":
                cells[6].get_text(
                    strip=True
                ),

            "rain_1h":
                cells[7].get_text(
                    strip=True
                ),

            "visibility":
                cells[8].get_text(
                    strip=True
                )
        })


    return result