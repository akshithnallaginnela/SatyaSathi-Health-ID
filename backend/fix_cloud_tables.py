"""Drop and recreate tables that had wrong column types"""
import asyncio
from sqlalchemy import text
from database import engine, create_tables

async def main():
    async with engine.begin() as conn:
        print("Dropping tables with wrong types...")
        # Drop in reverse dependency order
        await conn.execute(text("DROP TABLE IF EXISTS user_settings CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS reports CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS vitals_log CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS body_metrics CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS daily_tasks CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS coin_ledger CASCADE"))
        print("✅ Dropped old tables")

    print("Recreating all tables with correct UUID types...")
    await create_tables()
    print("✅ All tables recreated successfully!")

if __name__ == "__main__":
    asyncio.run(main())
