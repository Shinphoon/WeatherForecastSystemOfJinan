import bcrypt
from fastapi import APIRouter, HTTPException, Header
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

class RegisterRequest(BaseModel):
    username: str
    nickname: str
    phone: str
    password: str

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

        return int(user_id)

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="登录已失效，请重新登录"
        )

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
            (username, password, nickname, phone)
            VALUES (?, ?, ?, ?)
            """,
            username,
            password_hash,
            nickname,
            phone
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
def login(data: LoginRequest):
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
                status
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

        return {
            "success": True,
            "message": "登录成功",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "phone": user.phone
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
                last_address,
                push_enable,
                status,
                create_time
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
            "avatar": user.avatar,
            "last_lng": user.last_lng,
            "last_lat": user.last_lat,
            "last_address": user.last_address,
            "push_enable": user.push_enable,
            "status": user.status,
            "create_time": (
                user.create_time.isoformat()
                if user.create_time
                else None
            )
        }

    finally:
        cursor.close()
        conn.close()