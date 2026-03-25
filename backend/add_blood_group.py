"""
Migration script to add blood_group column to users table
"""
import asyncio
from database import get_db_session

async def add_blood_group_column():
    """Add blood_group column to users table if it doesn't exist"""
    async with get_db_session() as db:
        try:
            # Check if column exists
            result = await db.execute("SELECT blood_group FROM users LIMIT 1")
            print("✓ blood_group column already exists")
        except Exception:
            # Column doesn't exist, add it
            print("Adding blood_group column...")
            await db.execute("ALTER TABLE users ADD COLUMN blood_group VARCHAR(5)")
            await db.commit()
            print("✓ blood_group column added successfully")

if __name__ == "__main__":
    asyncio.run(add_blood_group_column())
