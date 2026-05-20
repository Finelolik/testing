import os
from dotenv import load_dotenv

load_dotenv()

import aiosqlite
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db, get_db, DB_PATH
from .auth import verify_password, create_access_token, ensure_default_admin
from .models import AdminLogin, TokenResponse
from .appeals import router as appeals_router
from .admins import router as admins_router

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_default_admin(db)
    yield


app = FastAPI(title="Портал обращений граждан", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://studvpn.alwaysdata.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(appeals_router)
app.include_router(admins_router)

@app.post("/api/admin/login", response_model=TokenResponse)
async def admin_login(data: AdminLogin, db=Depends(get_db)):
    cursor = await db.execute(
        "SELECT password_hash FROM admins WHERE username = ?", (data.username,)
    )
    row = await cursor.fetchone()

    if not row or not verify_password(data.password, row[0]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )

    token = create_access_token({"sub": data.username})
    return {"access_token": token}

app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")


@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/admin")
async def serve_admin():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin.html"))