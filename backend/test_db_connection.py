"""Test cloud database connection"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    DATABASE_URL = os.getenv("DATABASE_URL")
    print(f"Testing connection to: {DATABASE_URL[:50]}...")
    
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        async with engine.connect() as conn:
            result = await conn.execute("SELECT 1")
            print("✅ Connection successful!")
            print(f"✅ Database is responding")
        await engine.dispose()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
