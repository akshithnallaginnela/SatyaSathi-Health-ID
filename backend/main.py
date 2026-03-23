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
# from routers.dashboard import router as dashboard_router
# from routers.tasks import router as tasks_router
# from routers.ocr import router as ocr_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create database tables
    await create_tables()
    print("✅ Database tables created (domain-first)")
    yield
    print("👋 Shutting down")

app = FastAPI(
    title="VitalID Backend",
    description="Preventive Healthcare Engine",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routers ───
app.include_router(auth_router)
app.include_router(vitals_router)

# Note: Other routers (dashboard, tasks, reports) will be added as they are redesigned 
# to use the new domain-first schema.

_uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(_uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "VitalID-Engine-V2"}

@app.get("/")
async def root():
    return {"message": "VitalID Preventive Health Engine V2"}
