import os
import json
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from wechat_service import (get_wechat_article, update_wechat_article_url)
from qweather_spider import get_realtime_weather, get_today_weather, get_station_info
from forecast_service import get_24h_forecast, get_2h_forecast, get_7d_forecast
from ground_image_service import find_latest_ground_image
from alert_service import (get_current_alert_summary,set_mock_alert,clear_mock_alert)
from auth import router as auth_router
from database import get_connection

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

app = FastAPI()

app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://172.20.10.4:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_stations():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                station_id,
                station_name,
                lng,
                lat,
                altitude
            FROM dbo.weather_station
            WHERE status = 1
            ORDER BY station_id
            """
        )

        rows = cursor.fetchall()

        return [
            {
                "id": str(row.station_id).strip(),
                "name": row.station_name,
                "lon": float(row.lng),
                "lat": float(row.lat),
                "alt": (
                    float(row.altitude)
                    if row.altitude is not None
                    else None
                )
            }
            for row in rows
        ]

    finally:
        cursor.close()
        conn.close()


def check_station(station_id):
    stations = load_stations()

    valid_stations = {
        station["id"]
        for station in stations
    }

    if station_id not in valid_stations:
        raise HTTPException(
            status_code=404,
            detail="未知气象站"
        )


def get_station(station_id):
    stations = load_stations()

    for station in stations:
        if station["id"] == station_id:
            return station

    raise HTTPException(
        status_code=404,
        detail="未知气象站"
    )

@app.get("/")
def root():
    return {
        "message": "济南天气系统后端运行成功"
    }

@app.get("/weather/stations")
def station_list():
    stations = load_stations()

    return [
        {
            "station": station["id"],
            "name": station["name"],
            "lat": station["lat"],
            "lon": station["lon"],
            "alt": station["alt"]
        }
        for station in stations
    ]

@app.get("/weather/station/{station_id}/realtime")
def station_realtime(station_id: str):
    check_station(station_id)
    return get_realtime_weather(
        station_id
    )

@app.get("/weather/station/{station_id}/today")
def station_today(station_id: str):
    check_station(station_id)
    return get_today_weather(
        station_id
    )

# 保留原来的济南实况接口
@app.get("/weather/jinan/realtime")
def jinan_realtime():
    return get_realtime_weather(
        "54823"
    )

@app.get("/weather/jinan/today")
def jinan_today():
    return get_today_weather(
        "54823"
    )

# 按气象站获取未来2小时预报
@app.get("/weather/forecast/2h/{station_id}")
def forecast_2h_by_station(station_id: str):
    station = get_station(
        station_id
    )
    return get_2h_forecast(
        latitude=station["lat"],
        longitude=station["lon"]
    )

# 按气象站获取未来24小时预报
@app.get("/weather/forecast/24h/{station_id}")
def forecast_24h_by_station(station_id: str):
    station = get_station(
        station_id
    )
    return get_24h_forecast(
        latitude=station["lat"],
        longitude=station["lon"]
    )

# 按气象站获取未来7天预报
@app.get("/weather/forecast/7d/{station_id}")
def forecast_7d_by_station(station_id: str):
    station = get_station(
        station_id
    )
    return get_7d_forecast(
        latitude=station["lat"],
        longitude=station["lon"]
    )

# 以下三个旧接口继续保留，默认返回济南预报
@app.get("/weather/forecast/2h")
def forecast_2h():
    return forecast_2h_by_station(
        "54823"
    )

@app.get("/weather/forecast/24h")
def forecast_24h():
    return forecast_24h_by_station(
        "54823"
    )

@app.get("/weather/forecast/7d")
def forecast_7d():
    return forecast_7d_by_station(
        "54823"
    )

@app.get("/weather/ground-image")
def get_ground_image():
    result = find_latest_ground_image()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="暂未找到最新济南实况图"
        )

    return result

@app.get("/weather/alerts/current")
def get_current_alerts():
    try:
        return get_current_alert_summary()

    except Exception as e:
        print("天气预警获取失败：", e)

        return {
            "has_alert": False,
            "count": 0,
            "latest": None,
            "error": "天气预警数据暂时获取失败"
        }

@app.post("/weather/alerts/mock")
def create_mock_alert():
    mock_alert = {
        "title": "济南市气象台发布暴雨橙色预警信号",
        "type": "暴雨",
        "level": "橙色",
        "sender": "济南市气象台",
        "area": "济南市",
        "publish_time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "description": (
            "模拟预警：预计未来3小时济南市部分地区"
            "可能出现较强降水，请注意防范。"
        ),
        "url": ""
    }

    set_mock_alert(mock_alert)

    return {
        "success": True,
        "message": "已开启模拟暴雨橙色预警",
        "alert": mock_alert
    }

@app.delete("/weather/alerts/mock")
def delete_mock_alert():
    clear_mock_alert()

    return {
        "success": True,
        "message": "模拟预警已取消"
    }

@app.get("/weather/wechat/latest")
def get_latest_wechat_article():
    return get_wechat_article()

from pydantic import BaseModel

class WechatArticleUpdate(BaseModel):
    url: str
    password: str

class StationCreate(BaseModel):
    station_id: str
    name: str
    lat: float
    lon: float
    password: str

@app.post("/weather/wechat/update")
def update_latest_wechat_article(
    data: WechatArticleUpdate
):
    import os

    admin_password = os.getenv(
        "WECHAT_ADMIN_PASSWORD"
    )

    if not admin_password:
        return {
            "success": False,
            "error": "服务器未配置管理员密码"
        }

    if data.password != admin_password:
        return {
            "success": False,
            "error": "管理员密码错误"
        }

    return update_wechat_article_url(
        data.url
    )

@app.post("/weather/stations/add")
def add_station(data: StationCreate):
    admin_password = os.getenv(
        "WECHAT_ADMIN_PASSWORD"
    )

    if not admin_password:
        return {
            "success": False,
            "error": "服务器未配置管理员密码"
        }

    if data.password != admin_password:
        return {
            "success": False,
            "error": "管理员密码错误"
        }

    station_id = data.station_id.strip()
    name = data.name.strip()

    if not station_id.isdigit() or len(station_id) != 5:
        return {
            "success": False,
            "error": "国家站站号必须是5位数字"
        }

    if not name:
        return {
            "success": False,
            "error": "站点名称不能为空"
        }

    if not -90 <= data.lat <= 90:
        return {
            "success": False,
            "error": "纬度必须在 -90 到 90 之间"
        }

    if not -180 <= data.lon <= 180:
        return {
            "success": False,
            "error": "经度必须在 -180 到 180 之间"
        }

    stations = load_stations()

    for station in stations:
        if station["id"] == station_id:
            return {
                "success": False,
                "error": "该国家站已经存在"
            }

    new_station = {
        "id": station_id,
        "name": name,
        "lat": data.lat,
        "lon": data.lon
    }

    stations.append(new_station)

    save_stations(
        stations
    )

    return {
        "success": True,
        "message": "国家站添加成功",
        "station": new_station
    }