import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from wechat_service import (get_wechat_article, update_wechat_article_url)
from qweather_spider import get_realtime_weather, get_today_weather, get_station_info
from forecast_service import get_24h_forecast, get_2h_forecast, get_7d_forecast
from ground_image_service import find_latest_ground_image
from alert_service import (get_current_alert_summary,set_mock_alert,clear_mock_alert)
from auth import router as auth_router
from admin_users import router as admin_users_router, require_admin
from feedback import router as feedback_router
from saved_locations import router as saved_locations_router
from zibo_products import router as zibo_products_router
from station_fields import collector as field_collector
from database import get_connection
from station_cities import station_city
from fastapi.responses import StreamingResponse
from himawari_service import get_shandong_himawari
from radar_alert_service import ( get_nearest_radar_echo,get_radar_approach )
from email_service import send_radar_email
from auth import get_token_user
from radar_email_worker import (check_all_users)
from pydantic import BaseModel, Field
from ai_service import (ask_deepseek)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

app = FastAPI()
app.include_router(saved_locations_router)
app.include_router(zibo_products_router)
from report_schedule import router as report_schedule_router, check_all_reports
app.include_router(report_schedule_router)

async def report_loop():
    while True:
        try: await asyncio.to_thread(check_all_reports)
        except Exception:
            import logging
            logging.getLogger(__name__).exception('Weather report scheduler failed')
        await asyncio.sleep(60)

@app.on_event('startup')
async def start_report_loop():
    app.state.report_task = asyncio.create_task(report_loop())

@app.on_event('shutdown')
async def stop_report_loop():
    task = getattr(app.state, 'report_task', None)
    if task:
        task.cancel()
        try: await task
        except asyncio.CancelledError: pass


async def radar_email_loop():
    while True:
        try:
            await asyncio.to_thread(
                check_all_users
            )

        except Exception as e:
            print(
                "[雷达邮件] 自动任务异常：",
                repr(e)
            )

        # 每5分钟检查一次
        await asyncio.sleep(300)

class AIChatRequest(BaseModel):
    message: str

    history: list[dict] = Field(
        default_factory=list
    )

    station_id: str | None = None
    lat: float | None = None
    lng: float | None = None


@app.post("/ai/chat")
def ai_chat(
    data: AIChatRequest
):
    message = data.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="请输入问题"
        )

    context = {}

    try:
        # =================================
        # 1. 确定用户想查询哪个气象站
        # =================================

        target_station_id = data.station_id

        stations = load_stations()

        # 如果用户问题中明确提到了站名，
        # 则优先使用用户问题中的地点
        for item in stations:

            station_name = item.get(
                "name"
            )

            if (
                station_name
                and station_name in message
            ):
                target_station_id = (
                    item["id"]
                )

                break

        # =================================
        # 2. 获取国家站天气数据
        # =================================

        if target_station_id:

            station = get_station(
                target_station_id
            )

            context[
                "current_station"
            ] = {
                "id":
                    station["id"],

                "name":
                    station["name"],

                "lat":
                    station["lat"],

                "lon":
                    station["lon"],

                "alt":
                    station.get("alt")
            }

            # -------------------------
            # 实时天气
            # -------------------------

            try:
                realtime = (
                    get_realtime_weather(
                        target_station_id
                    )
                )

                context[
                    "realtime"
                ] = realtime

            except Exception as e:

                print(
                    "AI获取实时天气失败：",
                    repr(e)
                )

                context[
                    "realtime_error"
                ] = str(e)

            # -------------------------
            # 未来2小时预报
            # -------------------------

            try:
                forecast_2h = (
                    get_2h_forecast(
                        latitude=
                            station["lat"],

                        longitude=
                            station["lon"]
                    )
                )

                context[
                    "forecast_2h"
                ] = forecast_2h

            except Exception as e:

                print(
                    "AI获取2小时预报失败：",
                    repr(e)
                )

                context[
                    "forecast_2h_error"
                ] = str(e)

            # -------------------------
            # 未来24小时预报
            # -------------------------

            try:
                forecast_24h = (
                    get_24h_forecast(
                        latitude=
                            station["lat"],

                        longitude=
                            station["lon"]
                    )
                )

                context[
                    "forecast_24h"
                ] = forecast_24h

            except Exception as e:

                print(
                    "AI获取24小时预报失败：",
                    repr(e)
                )

                context[
                    "forecast_24h_error"
                ] = str(e)

            # -------------------------
            # 未来7天预报
            # -------------------------

            try:
                forecast_7d = (
                    get_7d_forecast(
                        latitude=
                            station["lat"],

                        longitude=
                            station["lon"]
                    )
                )

                context[
                    "forecast_7d"
                ] = forecast_7d

            except Exception as e:

                print(
                    "AI获取7天预报失败：",
                    repr(e)
                )

                context[
                    "forecast_7d_error"
                ] = str(e)

        else:

            context[
                "station_error"
            ] = "当前没有可用的国家气象站"

        # =================================
        # 3. 用户当前位置
        # =================================

        if (
            data.lat is not None
            and data.lng is not None
        ):

            context[
                "user_location"
            ] = {
                "lat": data.lat,
                "lng": data.lng
            }

            # =================================
            # 4. 雷达降水回波分析
            # =================================

            try:
                radar = (
                    get_radar_approach(
                        data.lat,
                        data.lng
                    )
                )

                context[
                    "radar"
                ] = radar

            except Exception as e:

                print(
                    "AI获取雷达分析失败：",
                    repr(e)
                )

                context[
                    "radar_error"
                ] = str(e)

        # =================================
        # 5. 调用 DeepSeek
        # =================================

        print(
            "AI使用气象站：",
            target_station_id
        )

        print(
            "AI天气上下文：",
            context
        )

        def generate_ai_stream():
            try:
                stream = ask_deepseek(
                    message,
                    data.history,
                    context,
                    stream=True
                )

                for chunk in stream:

                    if not chunk.choices:
                        continue

                    content = (
                        chunk
                        .choices[0]
                        .delta
                        .content
                    )

                    if content:
                        yield content

            except Exception as e:
                print(
                    "DeepSeek流式输出失败：",
                    repr(e)
                )

                yield "\n\nAI助手暂时无法继续回答。"


        return StreamingResponse(
            generate_ai_stream(),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )

    except HTTPException:
        raise

    except Exception as e:

        print(
            "AI对话失败：",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "AI助手暂时无法回答："
                + str(e)
            )
        )

@app.on_event("startup")
async def start_radar_email_worker():
    print(
        "[雷达邮件] 自动推送服务已启动"
    )

    app.state.radar_email_task = (
        asyncio.create_task(
            radar_email_loop()
        )
    )


@app.on_event("shutdown")
async def stop_radar_email_worker():
    task = getattr(
        app.state,
        "radar_email_task",
        None
    )

    if task:
        task.cancel()

        try:
            await task

        except asyncio.CancelledError:
            pass

app.include_router(auth_router)
app.include_router(admin_users_router)
app.include_router(feedback_router)

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
                city,
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
                "city": station_city(row.station_id, row.city),
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

@app.post(
    "/weather/radar/email-test"
)
def radar_email_test(
    authorization: str = Header(default=None)
):
    user_id = get_token_user(
        authorization
    )

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                email,
                push_enable,
                last_lat,
                last_lng,
                last_address
            FROM dbo.sys_user
            WHERE id = ?
            """,
            user_id
        )

        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="用户不存在"
            )

        if not user.email:
            raise HTTPException(
                status_code=400,
                detail="尚未绑定邮箱"
            )

        if not user.push_enable:
            raise HTTPException(
                status_code=400,
                detail="天气推送未开启"
            )

        if (
            user.last_lat is None
            or user.last_lng is None
        ):
            raise HTTPException(
                status_code=400,
                detail="尚未保存位置"
            )

        result = get_radar_approach(
            float(user.last_lat),
            float(user.last_lng)
        )

        status = result.get(
            "status"
        )

        if status not in [
            "raining",
            "approaching"
        ]:
            return {
                "success": True,
                "sent": False,
                "message":
                    "当前不满足降雨邮件推送条件",
                "radar": result
            }

        if (
            status == "approaching"
            and (
                result.get("eta_minutes")
                is None
                or result["eta_minutes"] > 60
            )
        ):
            return {
                "success": True,
                "sent": False,
                "message":
                    "预计降雨时间超过60分钟，暂不推送",
                "radar": result
            }

        try:
            send_radar_email(
                to_email=user.email,
                status=status,
                distance_km=result.get(
                    "distance_km"
                ),
                eta_minutes=result.get(
                    "eta_minutes"
                ),
                address=user.last_address
            )

        except Exception as e:
            print(
                "Gmail发送失败：",
                repr(e)
            )

            raise HTTPException(
                status_code=500,
                detail=f"Gmail发送失败：{e}"
            )
        return {
            "success": True,
            "sent": True,
            "message": "降雨提醒邮件已发送",
            "radar": result
        }

    finally:
        cursor.close()
        conn.close()

@app.get(
    "/weather/radar/nearest"
)
def radar_nearest(
    lat: float,
    lng: float
):
    if not -90 <= lat <= 90:
        raise HTTPException(
            status_code=400,
            detail="纬度不合法"
        )

    if not -180 <= lng <= 180:
        raise HTTPException(
            status_code=400,
            detail="经度不合法"
        )

    try:
        return (
            get_nearest_radar_echo(
                lat,
                lng
            )
        )

    except Exception as e:
        print(
            "雷达回波距离计算失败：",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="雷达回波距离计算失败"
        )

@app.get(
    "/weather/radar/approach"
)
def radar_approach(
    lat: float,
    lng: float
):
    try:
        return get_radar_approach(
            lat,
            lng
        )

    except Exception as e:
        print(
            "雷达趋势分析失败：",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="雷达趋势分析失败"
        )

@app.get("/weather/stations")
def station_list():
    stations = load_stations()

    return [
        {
            "station": station["id"],
            "name": station["name"],
            "city": station["city"],
            "lat": station["lat"],
            "lon": station["lon"],
            "alt": station["alt"]
        }
        for station in stations
    ]

@app.get('/weather/station-fields')
def station_fields(changes: bool = False):
    return field_collector.snapshot(load_stations(), changes)

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

class MockAlertRequest(BaseModel):
    alert_type: str
    level: str
    area: str = "济南市"
    sender: str = "济南市气象台"
    description: str = ""

@app.post("/weather/alerts/mock")
def create_mock_alert(data: MockAlertRequest):
    alert_type = data.alert_type.strip()
    level = data.level.strip()

    valid_levels = [
        "蓝色",
        "黄色",
        "橙色",
        "红色"
    ]

    if level not in valid_levels:
        raise HTTPException(
            status_code=400,
            detail="预警级别必须为蓝色、黄色、橙色或红色"
        )

    description = data.description.strip()

    if not description:
        description = (
            f"模拟预警：{data.area}当前发布"
            f"{alert_type}{level}预警信号，"
            f"请注意防范相关气象灾害。"
        )

    mock_alert = {
        "title": (
            f"{data.sender}发布"
            f"{alert_type}{level}预警信号"
        ),
        "type": alert_type,
        "level": level,
        "sender": data.sender,
        "area": data.area,
        "publish_time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "description": description,
        "url": ""
    }

    set_mock_alert(mock_alert)

    return {
        "success": True,
        "message": (
            f"已开启模拟"
            f"{alert_type}{level}预警"
        ),
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


class WechatArticleUpdate(BaseModel):
    url: str

class StationCreate(BaseModel):
    station_id: str
    name: str
    lat: float
    lon: float

@app.post("/weather/wechat/update")
def update_latest_wechat_article(
    data: WechatArticleUpdate, authorization: str = Header(default=None)
):
    require_admin(authorization)

    return update_wechat_article_url(
        data.url
    )

@app.post("/weather/stations/add")
def add_station(data: StationCreate, authorization: str = Header(default=None)):
    require_admin(authorization)

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

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT station_id
            FROM dbo.weather_station
            WHERE station_id = ?
            """,
            station_id
        )

        if cursor.fetchone():
            return {
                "success": False,
                "error": "该国家站已经存在"
            }

        cursor.execute(
            """
            INSERT INTO dbo.weather_station
            (
                station_id,
                station_name,
                station_type,
                province,
                city,
                district,
                lng,
                lat,
                altitude,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            station_id,
            name,
            1,
            "未知",
            "未知",
            "未知",
            data.lon,
            data.lat,
            None,
            1
        )

        conn.commit()

        return {
            "success": True,
            "message": "国家站添加成功",
            "station": {
                "id": station_id,
                "name": name,
                "lat": data.lat,
                "lon": data.lon
            }
        }

    except Exception as e:
        conn.rollback()

        print("添加国家站失败：", e)

        raise HTTPException(
            status_code=500,
            detail="添加国家站失败"
        )

    finally:
        cursor.close()
        conn.close()

@app.get("/weather/satellite/shandong")
def shandong_satellite():
    image = get_shandong_himawari()

    return StreamingResponse(
        image,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-cache"
        }
    )
