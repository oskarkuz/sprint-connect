"""Authentication module for Sprint Connect"""

from datetime import datetime, timedelta
from typing import Optional
import os
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import models
import schemas
from database import get_db

# -------- Security configuration --------
# Забираем секрет из окружения, иначе дефолт для разработки
# Можно хранить в .env: SECRET_KEY="super-long-random-string"
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production-please")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7 days

# -------- Password hashing --------
# bcrypt_sha256 сначала делает sha256 пароля, затем bcrypt — нет лимита в 72 байта
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

# -------- OAuth2 schemes --------
# Базовая схема для обязательной аутентификации
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# Опциональная схема (не бросает 401, если заголовка нет)
oauth2_optional_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def authenticate_user(db: Session, email: str, password: str):
    """Authenticate a user by email and password"""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    """Ensure the current user is active"""
    # Убедись, что в модели User есть поле is_active (bool) с дефолтом True
    if hasattr(current_user, "is_active") and not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_admin_user(current_user: models.User = Depends(get_current_active_user)):
    """Ensure the current user is an admin"""
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_optional_user(
    token: Optional[str] = Depends(oauth2_optional_scheme),
    db: Session = Depends(get_db),
):
    """Get the current user if authenticated, otherwise return None"""
    if not token:
        return None
    try:
        return await get_current_user(token, db)
    except Exception:
        return None