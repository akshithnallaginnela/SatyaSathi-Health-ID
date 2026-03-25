"""
Migration script to add blood_group column to users table
"""
import asyncio
from sqlalchemy import text
from database import engine

async def add_blood_group_column():
    """Add blood_group column to users table if it doesn't exist"""
    try:
        async with engine.begin() as conn:
            # Try to add the column directly
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS blood_group VARCHAR(5)"))
            print("✓ blood_group column added successfully")
    except Exception as e:
        if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
            print("✓ blood_group column already exists")
        else:
            print(f"Error: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(add_blood_group_column())
