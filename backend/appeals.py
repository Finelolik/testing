from fastapi import APIRouter, Depends, HTTPException, status, Request
import logging

from .database import get_db
from .models import AppealCreate, AppealResponse
from .auth import get_current_admin
from .limiter import limiter

router = APIRouter(prefix="/api/appeals", tags=["appeals"])
api_logger = logging.getLogger("appeals_api")
security_logger = logging.getLogger("appeals_api.security")

@router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_appeal(request: Request, appeal: AppealCreate, db=Depends(get_db)):
    cursor = await db.execute(
        """INSERT INTO appeals (full_name, phone, email, subject, body)
        VALUES (?, ?, ?, ?, ?)""",
        (appeal.full_name, appeal.phone, appeal.email, appeal.subject, appeal.body),
    )
    await db.commit()
    api_logger.info(
        f"Новое обращение | id: {cursor.lastrowid} | "
        f"email: {appeal.email} | тема: {appeal.subject[:30]}"
    )
    return {"id": cursor.lastrowid, "message": "Обращение успешно отправлено"}

@router.get("/", dependencies=[Depends(get_current_admin)])
@limiter.limit("60/minute")
async def list_appeals(
    request: Request,
    status: str = "active",
    skip: int = 0,
    limit: int = 20,
    db=Depends(get_db),
):
    cursor = await db.execute(
        """SELECT * FROM appeals WHERE status = ?
        ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?""",
        (status, limit, skip),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]

@router.get("/count", dependencies=[Depends(get_current_admin)])
@limiter.limit("60/minute")
async def count_appeals(request: Request, status: str = "active", db=Depends(get_db)):
    cursor = await db.execute(
        "SELECT COUNT(*) FROM appeals WHERE status = ?", (status,)
    )
    row = await cursor.fetchone()
    return {"total": row[0]}

@router.get("/{appeal_id}", dependencies=[Depends(get_current_admin)])
@limiter.limit("60/minute")
async def get_appeal(request: Request, appeal_id: int, db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM appeals WHERE id = ?", (appeal_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Обращение не найдено")
    return dict(row)

@router.patch("/{appeal_id}/archive", dependencies=[Depends(get_current_admin)])
@limiter.limit("30/minute")
async def archive_appeal(request: Request, appeal_id: int, db=Depends(get_db)):
    cursor = await db.execute(
        "UPDATE appeals SET status = 'archived' WHERE id = ? AND status = 'active'",
        (appeal_id,),
    )
    await db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Обращение не найдено или уже в архиве")
    api_logger.info(f"Обращение архивировано | id: {appeal_id}")
    return {"message": "Перемещено в архив"}

@router.delete("/{appeal_id}", dependencies=[Depends(get_current_admin)])
@limiter.limit("30/minute")
async def delete_appeal(request: Request, appeal_id: int, db=Depends(get_db)):
    cursor = await db.execute("DELETE FROM appeals WHERE id = ?", (appeal_id,))
    await db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Обращение не найдено")
    security_logger.warning(f"Обращение удалено | id: {appeal_id}")
    return {"message": "Обращение удалено"}