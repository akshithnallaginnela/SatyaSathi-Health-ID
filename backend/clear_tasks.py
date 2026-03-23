import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete
from datetime import date
from dotenv import load_dotenv

# Add current dir to path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from models.domain import DailyTask

# Use DB URL from env or fallback
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./vitalid.db")

async def clear_tasks():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        today = date.today()
        # Delete incomplete tasks for today
        stmt = delete(DailyTask).where(
            DailyTask.task_date == today,
            DailyTask.completed == False
        )
        try:
            result = await session.execute(stmt)
            await session.commit()
            print(f"✓ Deleted {result.rowcount} incomplete tasks from today")
        except Exception as e:
            print(f"⚠ Could not clear tasks (likely fresh DB): {e}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(clear_tasks())
