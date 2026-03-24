import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from database import create_tables
from routers.auth import router as auth_router
from routers.vitals import router as vitals_router
from routers.dashboard import router as dashboard_router
from routers.tasks import router as tasks_router
from routers.reports import router as reports_router
from routers.profile import router as profile_router
from routers.settings import router as settings_router
from routers.clinics import router as clinics_router
from routers.coins import router as coins_router
from routers.notifications import router as notifications_router
try:
    from routers.diet import router as diet_router
    _has_diet = True
except Exception:
    _has_diet = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create database tables
    await create_tables()
    print("✅ Database tables created (domain-first)")
    yield
    print("👋 Shutting down")

app = FastAPI(
    title="VitalID Backend Engine",
    description="Preventive Healthcare Engine V2.0",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173", # Vite default
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routers ───
app.include_router(auth_router)
app.include_router(vitals_router)
app.include_router(dashboard_router)
app.include_router(tasks_router)
app.include_router(reports_router)
app.include_router(profile_router)
app.include_router(settings_router)
app.include_router(clinics_router)
app.include_router(coins_router)
app.include_router(notifications_router)
if _has_diet:
    app.include_router(diet_router)

# Legacy alias: /api/ml/analyze-report → /api/reports/analyze
from routers.reports import analyze_report
from fastapi import UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from security.jwt_handler import get_current_user_id

@app.post("/api/ml/analyze-report")
async def legacy_analyze_report(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await analyze_report(file, user_id, db)

_uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(_uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "VitalID-Engine-V2"}

@app.get("/")
async def root():
    return {"message": "VitalID Preventive Health Engine V2"}
