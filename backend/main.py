"""
Health ID Backend — FastAPI application.
"""

import sys
import os

# Add backend directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

load_dotenv()

from database import create_tables

# Import all models to ensure they're registered with SQLAlchemy
from models.user import User
from models.health_record import VitalsLog, BodyMetrics
from models.report import Report
from models.task import DailyTask
from models.coin_ledger import CoinLedger
from models.user_settings import UserSettings
from security.audit_log import AuditLog

# Import routers
from routers.auth import router as auth_router
from routers.vitals import router as vitals_router
from routers.dashboard import router as dashboard_router
from routers.tasks import router as tasks_router
from routers.coins import router as coins_router
from routers.profile import router as profile_router
from routers.ocr import router as ocr_router
from routers.clinics import router as clinics_router
from routers.ml import router as ml_router
from routers.reports import router as reports_router
from routers.settings import router as settings_router
from routers.notifications import router as notifications_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    # Startup: create database tables
    await create_tables()
    print("✅ Database tables created")
    print("🚀 VitalID backend is running!")
    yield
    # Shutdown
    print("👋 VitalID backend shutting down")


app = FastAPI(
    title="VitalID Health Analytics API",
    description="Preventive healthcare backend with health analytics, daily tasks, coin rewards, and blockchain integration.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routers ───
app.include_router(auth_router)
app.include_router(vitals_router)
app.include_router(dashboard_router)
app.include_router(tasks_router)
app.include_router(coins_router)
app.include_router(profile_router)
app.include_router(ocr_router)
app.include_router(clinics_router)
app.include_router(ml_router)
app.include_router(reports_router)
app.include_router(settings_router)
app.include_router(notifications_router)

# Serve locally-uploaded profile photos
_uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(_uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")


# ─── Health Check ───
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "VitalID Backend",
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    return {
        "message": "VitalID Health Analytics API",
        "docs": "/docs",
        "health": "/api/health",
    }
