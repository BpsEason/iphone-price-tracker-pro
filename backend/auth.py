import os
import logging
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request  # 💡 引入 Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional

# 💡 確保引入你的資料庫模型與 SessionLocal
from database import SessionLocal
from models import User

# --- 配置區 ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-for-dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__ident="2b"  
)

# 用於 Swagger UI 登入
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False) 

# --- 資料庫依賴 ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 工具函式 ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if len(plain_password.encode('utf-8')) > 72:
            plain_password = plain_password[:72]
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logging.error(f"❌ 密碼驗證異常: {e}")
        return False

def get_password_hash(password: str) -> str:
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- 核心驗證邏輯 ---

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    """
    強制驗證：用於需要登入才能操作的 API (如：新增收藏、觸發爬蟲)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_user_optional(
    request: Request, # 💡 直接從 Request 拿 Header，避開 OAuth2Bearer 的強制錯誤
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    非強制驗證：用於產品列表。
    如果有正確 Token 就回傳 User，其餘情況（沒帶、過期、錯誤）一律回傳 None。
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        
        user = db.query(User).filter(User.email == email).first()
        return user
    except (JWTError, IndexError, Exception):
        # 💡 這裡發生任何錯誤都不報錯，直接當作未登入訪客
        return None