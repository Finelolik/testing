import os
import time
import logging
from dotenv import load_dotenv

load_dotenv()

import aiosqlite
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db, get_db, DB_PATH
from .auth import verify_password, create_access_token, ensure_default_admin
from .models import AdminLogin, TokenResponse
from .appeals import router as appeals_router
from .admins import router as admins_router
from .logging_config import setup_logging

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

# Настройка логирования
api_logger, security_logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_default_admin(db)
    api_logger.info("Приложение запущено, БД инициализирована")
    yield
    api_logger.info("Приложение остановлено")

app = FastAPI(title="Портал обращений граждан", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://studvpn.alwaysdata.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MIDDLEWARE: логирование всех запросов ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    client = request.client.host if request.client else "unknown"

    response = await call_next(request)

    duration = time.time() - start
    api_logger.info(
        f"{client} | {request.method} {request.url.path} | "
        f"HTTP {response.status_code} | {duration:.3f}s"
    )
    return response

app.include_router(appeals_router)
app.include_router(admins_router)

@app.post("/api/admin/login", response_model=TokenResponse)
async def admin_login(data: AdminLogin, request: Request, db=Depends(get_db)):
    cursor = await db.execute(
        "SELECT password_hash FROM admins WHERE username = ?", (data.username,)
    )
    row = await cursor.fetchone()
    client = request.client.host if request.client else "unknown"

    if not row or not verify_password(data.password, row[0]):
        security_logger.warning(
            f"Неудачный вход | логин: {data.username} | IP: {client}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )

    token = create_access_token({"sub": data.username})
    security_logger.info(
        f"Успешный вход | админ: {data.username} | IP: {client}"
    )
    return {"access_token": token}

app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/admin")
async def serve_admin():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin.html"))