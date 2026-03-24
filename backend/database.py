"""
Database configuration and session management.
Uses SQLite for local development, easily swappable to PostgreSQL.
"""

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

load_dotenv()

# PostgreSQL first, but defaults to async sqlite for local testing if no env var is provided
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./vitalid.db")

# Source of truth for SQLAlchemy Base
from models.domain import Base

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def create_tables():
    from models.domain import Base
    from models.reminder import Reminder  # Ensure reminder table is created
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
