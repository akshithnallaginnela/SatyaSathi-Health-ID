"""Run analysis manually for the existing user to populate DB."""
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from models.domain import User
from ml.analysis_engine import (
    get_user, get_bp_readings, get_sugar_readings, get_latest_report,
    build_features, calculate_health_index, generate_preventive_care,
    generate_daily_tasks, generate_diet_plan,
    save_preventive_care, replace_todays_tasks, save_diet, update_analysis_status,
    run_full_analysis
)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./vitalid.db")

async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get first user
        result = await db.execute(select(User))
        user = result.scalar_one_or_none()
        if not user:
            print("No users found!")
            return
        
        user_id = str(user.id)
        print(f"User: {user.full_name} (ID: {user_id[:8]}...)")
        
        # Run analysis
        try:
            analysis = await run_full_analysis(user_id, db)
            await db.commit()
            print(f"\n✅ Analysis complete!")
            if analysis:
                print(f"  Health Index: {analysis['health_index']}")
                print(f"  Tasks: {len(analysis['tasks'])}")
                print(f"  Preventive: {len(analysis['preventive_care'])}")
                print(f"  Diet: {analysis['diet'].get('focus_type') if analysis['diet'] else 'None'}")
            else:
                print("  ❌ Analysis returned None")
        except Exception as e:
            import traceback
            print(f"❌ Analysis ERROR: {e}")
            traceback.print_exc()
    
    await engine.dispose()

asyncio.run(main())
