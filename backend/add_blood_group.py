"""
Migration script to add blood_group column to users table
"""
import asyncio
from sqlalchemy import text
from database import engine

async def add_blood_group_column():
    """Add blood_group column to users table if it doesn't exist"""
    async with engine.begin() as conn:
        try:
            # Check if column exists by trying to select it
            await conn.execute(text("SELECT blood_group FROM users LIMIT 1"))
            print("✓ blood_group column already exists")
        except Exception as e:
            # Column doesn't exist, add it
            print("Adding blood_group column...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN blood_group VARCHAR(5)"))
            print("✓ blood_group column added successfully")

if __name__ == "__main__":
    asyncio.run(add_blood_group_column())
