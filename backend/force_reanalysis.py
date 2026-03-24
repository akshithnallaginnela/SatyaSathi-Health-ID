"""
Force re-run analysis for all users to refresh preventive care with new logic
"""
import asyncio
from sqlalchemy import select
from database import async_session
from models.domain import User
from ml.analysis_engine import run_full_analysis

async def main():
    async with async_session() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        print(f"🔄 Re-analyzing {len(users)} users...")
        
        for user in users:
            print(f"\n👤 User: {user.full_name or user.email}")
            try:
                analysis = await run_full_analysis(user.id, db)
                if analysis:
                    print(f"   ✅ Health Index: {analysis['health_index']}")
                    print(f"   ✅ Care Items: {len(analysis['preventive_care'])}")
                    print(f"   ✅ Tasks: {len(analysis['tasks'])}")
                    if analysis['preventive_care']:
                        for item in analysis['preventive_care']:
                            print(f"      - {item['category']}: {item['current_status']}")
                else:
                    print(f"   ⚠️ No data to analyze")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        await db.commit()
        print(f"\n✅ Re-analysis complete!")

if __name__ == "__main__":
    asyncio.run(main())
