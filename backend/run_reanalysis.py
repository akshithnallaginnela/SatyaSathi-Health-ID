import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

USER_ID = 'a46da996-9c05-45dd-97a6-7623f46901bf'

async def main():
    from database import get_db
    from ml.analysis_engine import run_full_analysis
    async for db in get_db():
        result = await run_full_analysis(USER_ID, db)
        await db.commit()
        if result:
            print('Tasks:', len(result.get('tasks', [])))
            for t in result.get('tasks', []):
                print('  [' + t['task_type'] + '] ' + t['task_name'] + ' | coins: ' + str(t['coins_reward']))
            print()
            for c in result.get('preventive_care', []):
                print('  [' + c['urgency'] + '] ' + c['category'] + ': ' + c['current_status'])
        else:
            print('Analysis returned None')
        break

asyncio.run(main())
