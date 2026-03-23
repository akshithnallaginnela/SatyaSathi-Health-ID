import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete
from datetime import date
from models.task import DailyTask

DATABASE_URL = "sqlite+aiosqlite:///./health_db.db"

async def clear_tasks():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        today = date.today()
        stmt = delete(DailyTask).where(
            DailyTask.task_date == today,
            DailyTask.completed == False
        )
        result = await session.execute(stmt)
        await session.commit()
        print(f"✓ Deleted {result.rowcount} incomplete tasks from today")
    
    await engine.dispose()

asyncio.run(clear_tasks())
