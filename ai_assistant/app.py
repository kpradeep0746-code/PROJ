from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from api.chat import router as chat_router
from api.transcript import router as transcript_router
from api.notes import router as notes_router
from database.connection import init_db
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB and ensure data folders exist
    db_dir = os.path.dirname(settings.database_url.replace("sqlite+aiosqlite:///", ""))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    os.makedirs(settings.lecture_folder, exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    await init_db()
    yield


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    lifespan=lifespan
)

# Enable CORS for local testing if frontend/backend are hosted separately
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(transcript_router)
app.include_router(notes_router)

# Mount static files for UI
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def home():
    index_path = "static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": f"{settings.app_title} is running.",
        "ui_status": "Front-end files are being initialized."
    }
