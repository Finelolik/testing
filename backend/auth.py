from datetime import datetime, timedelta, timezone
from typing import Optional
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt

from .database import get_db

SECRET_KEY = os.environ["SECRET_KEY"]
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY должна быть задана в переменных окружения (.env)")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")

def hash_password(password: str) -> str:
    # bcrypt работает с bytes, обрезаем до 72 байт на всякий случай
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pwd_bytes = plain.encode("utf-8")[:72]
    hash_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(pwd_bytes, hash_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
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
