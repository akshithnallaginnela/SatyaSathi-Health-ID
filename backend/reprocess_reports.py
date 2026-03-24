"""Re-process existing reports through the improved OCR engine."""
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from models.domain import BloodReport
from services.ocr_service import extract_report_values
from ml.analysis_engine import run_full_analysis

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./vitalid.db")

async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get all reports
        result = await db.execute(select(BloodReport))
        reports = result.scalars().all()
        
        print(f"🔄 Re-processing {len(reports)} reports...")
        
        for r in reports:
            if not os.path.exists(r.file_path):
                print(f"  ❌ File missing: {r.file_path}")
                continue
            
            print(f"  ⚡ Analyzing: {os.path.basename(r.file_path)}")
            try:
                extracted = await extract_report_values(r.file_path)
                
                # Update report with new data
                r.hemoglobin = extracted.get("hemoglobin")
                r.platelet_count = extracted.get("platelet_count")
                r.fasting_glucose = extracted.get("fasting_glucose")
                r.random_glucose = extracted.get("random_glucose")
                r.creatinine = extracted.get("creatinine")
                r.urea = extracted.get("urea")
                r.lab_name = extracted.get("lab_name")
                
                print(f"    ✅ Extracted: Hb={r.hemoglobin}, Plt={r.platelet_count}, Glu={r.fasting_glucose}")
                
                # Trigger analysis to refresh tasks/care items based on new data
                await run_full_analysis(str(r.user_id), db)
                
            except Exception as e:
                print(f"    ❌ FAILED: {e}")
        
        await db.commit()
        print("\n✅ All reports re-processed and database updated!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
