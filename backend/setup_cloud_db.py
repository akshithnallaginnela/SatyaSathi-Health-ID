"""
Set up cloud PostgreSQL database with all tables
"""
import asyncio
from database import create_tables

async def main():
    print("🚀 Creating tables in cloud PostgreSQL database...")
    try:
        await create_tables()
        print("✅ All tables created successfully in Supabase!")
        print("\nTables created:")
        print("  - users")
        print("  - user_data_status")
        print("  - bp_readings")
        print("  - sugar_readings")
        print("  - blood_reports")
        print("  - health_signals")
        print("  - preventive_care")
        print("  - daily_tasks")
        print("  - diet_recommendations")
        print("  - coin_ledger")
        print("  - reminders")
        print("\n🎉 Database is ready!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
