from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import logging

from .database import get_db
from .auth import get_current_admin, hash_password
import os

router = APIRouter(prefix="/api/admins", tags=["admins"])
security_logger = logging.getLogger("appeals_api.security")

class AdminCreate(BaseModel):
    username: str
    password: str

class AdminUpdate(BaseModel):
    password: str

@router.get("/", dependencies=[Depends(get_current_admin)])
async def list_admins(skip: int = 0, limit: int = 50, db=Depends(get_db)):
    cursor = await db.execute(
        "SELECT id, username FROM admins ORDER BY id LIMIT ? OFFSET ?", (limit, skip)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]

@router.post("/", dependencies=[Depends(get_current_admin)], status_code=201)
async def create_admin(data: AdminCreate, db=Depends(get_db)):
    cursor = await db.execute("SELECT id FROM admins WHERE username = ?", (data.username,))
    existing = await cursor.fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    hashed = hash_password(data.password)
    await db.execute(
        "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
        (data.username, hashed),
    )
    await db.commit()
    security_logger.warning(f"Создан администратор | username: {data.username}")
    return {"message": "Администратор создан"}

@router.patch("/{admin_id}", dependencies=[Depends(get_current_admin)])
async def update_admin(admin_id: int, data: AdminUpdate, db=Depends(get_db)):
    cursor = await db.execute("SELECT username FROM admins WHERE id = ?", (admin_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Администратор не найден")
    hashed = hash_password(data.password)
    await db.execute(
        "UPDATE admins SET password_hash = ? WHERE id = ?",
        (hashed, admin_id),
    )
    await db.commit()
    security_logger.warning(
        f"Смена пароля | admin_id: {admin_id}, username: {row['username']}"
    )
    return {"message": "Пароль обновлён"}

@router.delete("/{admin_id}", dependencies=[Depends(get_current_admin)])
async def delete_admin(admin_id: int, db=Depends(get_db)):
    cursor = await db.execute("SELECT username FROM admins WHERE id = ?", (admin_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Администратор не найден")
    root_username = os.environ.get("ADMIN_USERNAME")
    if row["username"] == root_username:
        raise HTTPException(status_code=403, detail="Нельзя удалить главного администратора")
    await db.execute("DELETE FROM admins WHERE id = ?", (admin_id,))
    await db.commit()
    security_logger.warning(
        f"Удалён администратор | id: {admin_id}, username: {row['username']}"
    )
    return {"message": "Администратор удалён"}