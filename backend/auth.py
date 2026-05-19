from datetime import datetime, timedelta
from typing import Optional
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from .database import get_db

SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-only-for-dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_admin(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недействительный токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload: dict = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if not isinstance(username, str) or not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    cursor = await db.execute("SELECT id FROM admins WHERE username = ?", (username,))
    admin = await cursor.fetchone()
    if admin is None:
        raise credentials_exception
    return username


async def ensure_default_admin(db) -> None:
    cursor = await db.execute("SELECT COUNT(*) FROM admins")
    row = await cursor.fetchone()
    if row[0] == 0:
        password = os.environ.get("ADMIN_PASSWORD")
        username = os.environ.get("ADMIN_USERNAME")
        if not password or not username:
            raise RuntimeError("ADMIN_PASSWORD и ADMIN_USERNAME должны быть заданы в .env")
        hashed = hash_password(password)
        await db.execute(
            "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
            (username, hashed),
        )
        await db.commit()
