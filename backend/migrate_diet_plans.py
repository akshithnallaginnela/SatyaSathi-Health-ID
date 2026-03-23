"""
Migration script to add diet plans to existing reports.

Run this once to backfill diet plans for reports uploaded before the diet plan feature.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from database import get_async_session_maker
from models.report import Report


def _build_diet_plan(diet_focus: str, risk_level: str) -> dict:
    """Generate personalized diet plan based on ML predictions."""
    
    plan = {
        "focus": diet_focus or "balanced",
        "breakfast": [],
        "lunch": [],
        "dinner": [],
        "snacks": [],
        "avoid": [],
        "hydration": "Drink 8-10 glasses of water daily",
    }
    
    if diet_focus == "iron_rich" or diet_focus == "iron_and_low_sugar":
        plan["breakfast"] = [
            "Spinach paratha with curd",
            "Ragi porridge with jaggery",
            "Moong dal chilla with mint chutney",
        ]
        plan["lunch"] = [
            "Brown rice with dal palak and beetroot salad",
            "Roti with rajma curry and cucumber raita",
            "Quinoa pulao with mixed vegetables",
        ]
        plan["dinner"] = [
            "Vegetable khichdi with spinach",
            "Roti with chana masala and green salad",
            "Millet roti with palak paneer",
        ]
        plan["snacks"] = [
            "Roasted peanuts and jaggery",
            "Dates and almonds (4-5 pieces)",
            "Beetroot and carrot juice",
        ]
        plan["avoid"] = [
            "Tea/coffee immediately after meals",
            "Excessive calcium supplements with iron-rich meals",
        ]
    
    elif diet_focus == "diabetic_friendly":
        plan["breakfast"] = [
            "Oats upma with vegetables",
            "Moong dal chilla with green chutney",
            "Vegetable poha (light oil)",
        ]
        plan["lunch"] = [
            "Brown rice (small portion) with dal and salad",
            "Roti with mixed vegetable curry and curd",
            "Quinoa with grilled vegetables",
        ]
        plan["dinner"] = [
            "Vegetable soup with 1 roti",
            "Grilled paneer with sautéed vegetables",
            "Millet khichdi with cucumber raita",
        ]
        plan["snacks"] = [
            "Roasted chana (chickpeas)",
            "Cucumber and carrot sticks",
            "Buttermilk (no sugar)",
        ]
        plan["avoid"] = [
            "White rice, white bread, maida products",
            "Sugary drinks, sweets, and desserts",
            "Fried foods and processed snacks",
        ]
    
    else:  # balanced or general_wellness
        plan["breakfast"] = [
            "Idli with sambar and coconut chutney",
            "Whole wheat toast with peanut butter",
            "Vegetable upma with curd",
        ]
        plan["lunch"] = [
            "Rice with dal, vegetable curry, and salad",
            "Roti with paneer curry and curd",
            "Mixed vegetable pulao with raita",
        ]
        plan["dinner"] = [
            "Light khichdi with vegetables",
            "Roti with dal and green vegetables",
            "Vegetable soup with whole wheat bread",
        ]
        plan["snacks"] = [
            "Fresh fruits (apple, banana, orange)",
            "Roasted nuts (almonds, walnuts)",
            "Sprouts salad",
        ]
        plan["avoid"] = [
            "Excessive fried and processed foods",
            "Too much salt and sugar",
        ]
    
    if risk_level == "high":
        plan["note"] = "⚠️ Consult your doctor before making major dietary changes. This is a general guideline."
    else:
        plan["note"] = "💡 This is a personalized suggestion. Adjust portions based on your activity level."
    
    return plan


async def migrate_diet_plans():
    """Add diet plans to all existing reports that don't have them."""
    
    SessionLocal = get_async_session_maker()
    async with SessionLocal() as db:
        # Get all reports
        result = await db.execute(select(Report))
        reports = result.scalars().all()
        
        updated_count = 0
        skipped_count = 0
        
        for report in reports:
            if not isinstance(report.extracted_values, dict):
                print(f"⚠️  Skipping report {report.id} - invalid extracted_values format")
                skipped_count += 1
                continue
            
            # Check if diet plan already exists
            if report.extracted_values.get("diet_plan"):
                print(f"✓ Report {report.id} already has diet plan")
                skipped_count += 1
                continue
            
            # Get ML analysis
            ml_analysis = report.extracted_values.get("ml_analysis") or {}
            diet_focus = ml_analysis.get("diet_focus", "balanced")
            risk_level = ml_analysis.get("risk_level", "low")
            
            # Generate diet plan
            diet_plan = _build_diet_plan(diet_focus, risk_level)
            
            # Update report
            report.extracted_values["diet_plan"] = diet_plan
            db.add(report)
            
            print(f"✅ Added diet plan to report {report.id} (focus: {diet_focus}, risk: {risk_level})")
            updated_count += 1
        
        # Commit all changes
        await db.commit()
        
        print("\n" + "="*60)
        print(f"Migration complete!")
        print(f"  ✅ Updated: {updated_count} reports")
        print(f"  ⏭️  Skipped: {skipped_count} reports")
        print("="*60)


if __name__ == "__main__":
    print("🔄 Starting diet plan migration...")
    print("="*60)
    asyncio.run(migrate_diet_plans())
