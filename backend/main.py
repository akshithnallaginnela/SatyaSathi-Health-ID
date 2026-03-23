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

# Note: Additional routers like clinics, notifications, profile can be migrated 
# as needed or kept if they don't break the new domain schema.

_uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(_uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "VitalID-Engine-V2"}

@app.get("/")
async def root():
    return {"message": "VitalID Preventive Health Engine V2"}
