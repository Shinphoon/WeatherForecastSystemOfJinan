import bcrypt
import math
import requests
from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from daily_briefing import inbox as briefing_inbox, mark_read as briefing_mark_read
from report_schedule import ensure_reports as ensure_daily_briefing
from rain_notifications import check_rain, inbox as rain_inbox, mark_read as rain_mark_read

def inbox(user_id):
    return sorted(briefing_inbox(user_id) + rain_inbox(user_id), key=lambda m: m["publish_time"], reverse=True)

def mark_read(user_id, ids):
    briefing_mark_read(user_id, ids)
    rain_mark_read(user_id, ids)
from pydantic import BaseModel
from database import get_connection
from jose import jwt, JWTError
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["用户认证"])

SECRET_KEY = "jinan-weather-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

class LoginRequest(BaseModel):
    username: str
    password: str


class NotificationReadRequest(BaseModel):
    ids: list[str]


@router.post('/daily-briefing')
def generate_daily_briefing(background_tasks: BackgroundTasks, authorization: str = Header(default=None)):
    user_id = get_token_user(authorization)
    background_tasks.add_task(check_rain, user_id)
    background_tasks.add_task(ensure_daily_briefing, user_id)
    return {'messages': inbox(user_id)}


@router.get('/notifications')
def notifications(authorization: str = Header(default=None)):
    return {'messages': inbox(get_token_user(authorization))}


@router.put('/notifications/read')
def read_notifications(data: NotificationReadRequest, authorization: str = Header(default=None)):
    user_id = get_token_user(authorization)
    mark_read(user_id, data.ids)
    return {'messages': inbox(user_id)}

class RegisterRequest(BaseModel):
    username: str
    nickname: str
    phone: str
    password: str
    email: str | None = None

def verify_password(password: str, password_hash: str):
    return bcrypt.checkpw(
        password.encode('utf-8'),
        password_hash.encode('utf-8')
    )

def create_access_token(user_id: int, username: str):
    expire = datetime.utcnow() + timedelta(
        hours=ACCESS_TOKEN_EXPIRE_HOURS
    )
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": expire
    }
    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def get_token_user(authorization: str):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="未登录"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="无效的登录凭证"
        )

    token = authorization[7:]

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="登录凭证无效"
            )

        user_id = int(user_id)

    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="登录已失效，请重新登录"
        )

    # Token signatures alone do not reflect bans applied after login.
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM sys_user WHERE id = ?', user_id)
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail='账号不存在，请重新登录')
        if user.status != 1:
            raise HTTPException(status_code=403, detail='该账号已被禁用')
        return user_id
    finally:
        conn.close()

def hash_password(password: str):
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

@router.post("/register")
def register(data: RegisterRequest):
    username = data.username.strip()
    nickname = data.nickname.strip()
    phone = data.phone.strip()
    password = data.password

    if len(username) < 3 or len(username) > 20:
        raise HTTPException(status_code=400, detail="用户名长度应为3～20个字符")
    if not nickname:
        raise HTTPException(status_code=400, detail="昵称不能为空")
    if len(phone) != 11 or not phone.isdigit():
        raise HTTPException(status_code=400, detail="手机号格式不正确")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6位")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id FROM sys_user WHERE username = ?",
            username
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="用户名已存在")

        cursor.execute(
            "SELECT id FROM sys_user WHERE phone = ?",
            phone
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="手机号已注册")

        password_hash = hash_password(password)

        cursor.execute(
            """
            INSERT INTO sys_user
            (
                username,
                password,
                nickname,
                phone,
                email
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            data.username,
            hashed_password,
            data.nickname,
            data.phone,
            data.email.strip() if data.email else None
        )

        conn.commit()

        return {
            "success": True,
            "message": "注册成功",
            "username": username
        }

    except HTTPException:
        raise

    except Exception as e:
        conn.rollback()
        print("注册失败：", e)
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误"
        )

    finally:
        cursor.close()
        conn.close()

@router.post("/login")
def login(data: LoginRequest, background_tasks: BackgroundTasks):
    username = data.username.strip()
    password = data.password

    if not username or not password:
        raise HTTPException(
            status_code=400,
            detail="请输入用户名和密码"
        )

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                id,
                username,
                password,
                nickname,
                phone,
                status,
                role
            FROM sys_user
            WHERE username = ?
            """,
            username
        )

        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=400,
                detail="用户名或密码错误"
            )

        if user.status == 0:
            raise HTTPException(
                status_code=403,
                detail="该账号已被禁用"
            )

        if not verify_password(
            password,
            user.password
        ):
            raise HTTPException(
                status_code=400,
                detail="用户名或密码错误"
            )

        access_token = create_access_token(
            user.id,
            user.username
        )

        background_tasks.add_task(check_rain, user.id)
        background_tasks.add_task(ensure_daily_briefing, user.id)

        return {
            "success": True,
            "message": "登录成功",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "phone": user.phone,
                "role": user.role
            }
        }

    finally:
        cursor.close()
        conn.close()

@router.get("/me")
def get_me(
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
                id,
                username,
                nickname,
                phone,
                avatar,
                last_lng,
                last_lat,
                last_alt,
                location_update_time,
                last_address,
                push_enable,
                status,
                create_time,
                role,
                email
            FROM sys_user
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

        return {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "phone": user.phone,
            "email": user.email,
            "avatar": user.avatar,

            "last_lng": (
                float(user.last_lng)
                if user.last_lng is not None
                else None
            ),

            "last_lat": (
                float(user.last_lat)
                if user.last_lat is not None
                else None
            ),

            "last_alt": (
                float(user.last_alt)
                if user.last_alt is not None
                else None
            ),

            "last_address":
                user.last_address,

            "location_update_time": (
                user.location_update_time.isoformat()
                if user.location_update_time
                else None
            ),

            "push_enable":
                user.push_enable,

            "status":
                user.status,

            "role":
                user.role,

            "create_time": (
                user.create_time.isoformat()
                if user.create_time
                else None
            )
        }

    finally:
        cursor.close()
        conn.close()
class PasswordUpdateRequest(BaseModel):
    current_password: str
    new_password: str

class PhoneUpdateRequest(BaseModel):
    phone: str

class EmailUpdateRequest(BaseModel):
    email: str | None = None

@router.put("/email")
def update_email(
    data: EmailUpdateRequest,
    authorization: str = Header(default=None)
):
    user_id = get_token_user(authorization)

    email = None

    if data.email:
        email = data.email.strip().lower()

        if "@" not in email or "." not in email:
            raise HTTPException(
                status_code=400,
                detail="邮箱格式不正确"
            )

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if email:
            cursor.execute(
                """
                SELECT id
                FROM sys_user
                WHERE email = ?
                  AND id <> ?
                """,
                email,
                user_id
            )

            if cursor.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail="该邮箱已被其他账号使用"
                )

        cursor.execute(
            """
            UPDATE sys_user
            SET email = ?,
                update_time = GETDATE()
            WHERE id = ?
            """,
            email,
            user_id
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="用户不存在"
            )

        conn.commit()

        return {
            "success": True,
            "message": (
                "邮箱已删除"
                if email is None
                else "邮箱修改成功"
            ),
            "email": email
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        print("修改邮箱失败：", e)

        raise HTTPException(
            status_code=500,
            detail="邮箱修改失败"
        )

    finally:
        cursor.close()
        conn.close()

@router.put("/phone")
def update_phone(
    data: PhoneUpdateRequest,
    authorization: str = Header(default=None)
):
    user_id = get_token_user(authorization)
    phone = data.phone.strip()

    if len(phone) != 11 or not phone.isdigit():
        raise HTTPException(
            status_code=400,
            detail="手机号格式不正确"
        )

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM sys_user
            WHERE phone = ?
              AND id <> ?
            """,
            phone,
            user_id
        )

        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="该手机号已被其他账号使用"
            )

        cursor.execute(
            """
            UPDATE sys_user
            SET phone = ?,
                update_time = GETDATE()
            WHERE id = ?
            """,
            phone,
            user_id
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="用户不存在"
            )

        conn.commit()

        return {
            "success": True,
            "message": "手机号修改成功",
            "phone": phone
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        print("修改手机号失败：", e)

        raise HTTPException(
            status_code=500,
            detail="手机号修改失败"
        )

    finally:
        cursor.close()
        conn.close()

class LocationUpdateRequest(BaseModel):
    lng: float
    lat: float
    alt: float | None = None


def get_elevation(lat, lng):
    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/elevation",
            params={
                "latitude": lat,
                "longitude": lng
            },
            timeout=8
        )

        response.raise_for_status()

        data = response.json()

        elevations = data.get("elevation")

        if (
            isinstance(elevations, list)
            and len(elevations) > 0
        ):
            return float(elevations[0])

    except Exception as e:
        print("获取海拔失败：", e)

    return None

def get_location_name(lat, lng):
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": lat,
                "lon": lng,
                "format": "jsonv2",
                "zoom": 18,
                "addressdetails": 1,
                "layer": "address,poi",
                "accept-language": "zh-CN"
            },
            headers={
                "User-Agent":
                    "jinan-weather-course-project/1.0"
            },
            timeout=8
        )

        response.raise_for_status()

        data = response.json()

        name = data.get("name")

        if name:
            return name

        address = data.get(
            "address",
            {}
        )

        for key in [
            "amenity",
            "shop",
            "tourism",
            "leisure",
            "university",
            "college",
            "school",
            "building",
            "road",
            "neighbourhood",
            "suburb"
        ]:
            if address.get(key):
                return address[key]

        return data.get(
            "display_name",
            "未知位置"
        )

    except Exception as e:
        print(
            "获取位置名称失败：",
            e
        )

        return None

def calculate_distance(
    lat1,
    lng1,
    lat2,
    lng2
):
    earth_radius = 6371.0

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lat = lat2 - lat1
    delta_lng = math.radians(
        lng2 - lng1
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lng / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius * c


@router.put("/location")
def update_location(
    data: LocationUpdateRequest,
    authorization: str = Header(default=None)
):
    user_id = get_token_user(
        authorization
    )

    if not -180 <= data.lng <= 180:
        raise HTTPException(
            status_code=400,
            detail="经度不合法"
        )

    if not -90 <= data.lat <= 90:
        raise HTTPException(
            status_code=400,
            detail="纬度不合法"
        )

    altitude = data.alt

    if altitude is None:
        altitude = get_elevation(
            data.lat,
            data.lng
        )

    location_name = get_location_name(
    data.lat,
    data.lng
)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                station_id,
                station_name,
                lng,
                lat
            FROM dbo.weather_station
            WHERE status = 1
            """
        )

        stations = cursor.fetchall()

        nearest_station = None
        nearest_distance = None

        for station in stations:
            distance = calculate_distance(
                data.lat,
                data.lng,
                float(station.lat),
                float(station.lng)
            )

            if (
                nearest_distance is None
                or distance < nearest_distance
            ):
                nearest_distance = distance

                nearest_station = {
                    "id": str(
                        station.station_id
                    ).strip(),

                    "name":
                        station.station_name,

                    "lat":
                        float(station.lat),

                    "lng":
                        float(station.lng),

                    "distance_km":
                        round(distance, 2)
                }

        cursor.execute(
            """
            UPDATE dbo.sys_user
            SET
                last_lng = ?,
                last_lat = ?,
                last_alt = ?,
                last_address = ?,
                location_update_time = GETDATE(),
                update_time = GETDATE()
            WHERE id = ?
            """,
            data.lng,
            data.lat,
            altitude,
            location_name,
            user_id
        )

        conn.commit()

        return {
            "success": True,
            "lng": data.lng,
            "lat": data.lat,
            "alt": altitude,
            "address": location_name,
            "nearest_station":
                nearest_station
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        print("保存位置失败：", e)

        raise HTTPException(
            status_code=500,
            detail="位置保存失败"
        )

    finally:
        cursor.close()
        conn.close()

@router.put("/password")
def update_password(
    data: PasswordUpdateRequest,
    authorization: str = Header(default=None)
):
    user_id = get_token_user(authorization)

    if len(data.new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="新密码至少6位"
        )

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT password
            FROM sys_user
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

        if not verify_password(
            data.current_password,
            user.password
        ):
            raise HTTPException(
                status_code=400,
                detail="当前密码错误"
            )

        new_password_hash = hash_password(
                data.new_password
            )

        cursor.execute(
            """
            UPDATE sys_user
            SET password = ?,
                update_time = GETDATE()
            WHERE id = ?
            """,
            new_password_hash,
            user_id
        )

        conn.commit()

        return {
            "success": True,
            "message": "密码修改成功"
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        print("修改密码失败：", e)

        raise HTTPException(
            status_code=500,
            detail="密码修改失败"
        )

    finally:
        cursor.close()
        conn.close()

class PushSettingRequest(BaseModel):
    push_enable: bool

@router.put("/push-setting")
def update_push_setting(
    data: PushSettingRequest,
    authorization: str = Header(default=None)
):
    user_id = get_token_user(authorization)
    conn = get_connection()
    cursor = conn.cursor()

    try:
        push_value = 1 if data.push_enable else 0

        cursor.execute(
            """
            UPDATE sys_user
            SET push_enable = ?,
                update_time = GETDATE()
            WHERE id = ?
            """,
            push_value,
            user_id
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="用户不存在"
            )

        conn.commit()

        return {
            "success": True,
            "message": "天气预警推送设置已更新",
            "push_enable": push_value
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        print("更新预警推送设置失败：", e)

        raise HTTPException(
            status_code=500,
            detail="预警推送设置更新失败"
        )

    finally:
        cursor.close()
        conn.close()
