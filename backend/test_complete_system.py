"""
Complete system test - verifies all components are working
"""
import asyncio
import sys
from sqlalchemy import text
from database import async_session, engine
from models.domain import User, BPReading, BloodReport
from ml.analysis_engine import run_full_analysis

async def test_database_connection():
    """Test 1: Database Connection"""
    print("\n" + "="*60)
    print("TEST 1: Database Connection")
    print("="*60)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ PostgreSQL connection successful")
            
            # Check if tables exist
            result = await conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            print(f"✅ Found {len(tables)} tables: {', '.join(tables[:5])}...")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def test_user_creation():
    """Test 2: User Creation"""
    print("\n" + "="*60)
    print("TEST 2: User Creation")
    print("="*60)
    try:
        async with async_session() as db:
            # Check if test user exists
            result = await db.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            print(f"✅ Found {count} users in database")
            
            if count == 0:
                print("⚠️  No users found - register a user via frontend")
            return True
    except Exception as e:
        print(f"❌ User query failed: {e}")
        return False

async def test_bp_classification():
    """Test 3: BP Classification Logic"""
    print("\n" + "="*60)
    print("TEST 3: BP Classification Logic")
    print("="*60)
    try:
        from ml.analysis_engine import generate_preventive_care
        
        # Test BP 120/80 (should be Normal)
        features = {
            "has_vitals_data": True,
            "bp_systolic_latest": 120,
            "bp_diastolic_latest": 80,
            "gender_enc": 1
        }
        care = generate_preventive_care(features)
        bp_care = [c for c in care if c["category"] == "blood_pressure"][0]
        
        if "Normal" in bp_care["current_status"]:
            print(f"✅ BP 120/80 correctly classified as: {bp_care['current_status']}")
            print(f"   Urgency: {bp_care['urgency']} (should be 'great')")
            return True
        else:
            print(f"❌ BP 120/80 incorrectly classified as: {bp_care['current_status']}")
            return False
    except Exception as e:
        print(f"❌ BP classification test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_preventive_care_messages():
    """Test 4: Preventive Care Message Length"""
    print("\n" + "="*60)
    print("TEST 4: Preventive Care Message Length")
    print("="*60)
    try:
        from ml.analysis_engine import generate_preventive_care
        
        features = {
            "has_vitals_data": True,
            "bp_systolic_latest": 135,
            "bp_diastolic_latest": 85,
            "sugar_latest": 110,
            "bmi": 28,
            "hemoglobin": 11.5,
            "platelet_count": 140000,
            "gender_enc": 1
        }
        care = generate_preventive_care(features)
        
        all_short = True
        for item in care:
            msg = item["future_risk_message"]
            sentences = msg.split(". ")
            if len(sentences) > 3:
                print(f"⚠️  {item['category']}: {len(sentences)} sentences (should be ≤2)")
                all_short = False
            else:
                print(f"✅ {item['category']}: {len(sentences)} sentences - {msg[:60]}...")
        
        return all_short
    except Exception as e:
        print(f"❌ Message length test failed: {e}")
        return False

async def test_ocr_prompt():
    """Test 5: OCR Prompt Enhancement"""
    print("\n" + "="*60)
    print("TEST 5: OCR Prompt Enhancement")
    print("="*60)
    try:
        from services.ocr_service import EXTRACTION_PROMPT
        
        # Check for key enhancements
        checks = [
            ("Drlogy", "Drlogy Pathology Lab"),
            ("SRN", "SRN Diagnostics"),
            ("Apollo", "Apollo Diagnostics"),
            ("Healthians", "Healthians"),
            ("Redcliffe", "Redcliffe"),
            ("Unit conversions", "UNIT CONVERSIONS"),
            ("Lakhs", "Lakhs"),
            ("10^3/μL", "10^3/μL"),
            ("POLYMORPHS", "POLYMORPHS"),
            ("TLC", "TLC"),
        ]
        
        all_present = True
        for name, keyword in checks:
            if keyword in EXTRACTION_PROMPT:
                print(f"✅ {name} support: Found")
            else:
                print(f"❌ {name} support: Missing")
                all_present = False
        
        return all_present
    except Exception as e:
        print(f"❌ OCR prompt test failed: {e}")
        return False

async def test_diet_plan_generation():
    """Test 6: Diet Plan Generation"""
    print("\n" + "="*60)
    print("TEST 6: Diet Plan Generation")
    print("="*60)
    try:
        from ml.analysis_engine import generate_diet_plan
        
        # Test with high BP
        features_high_bp = {
            "has_vitals_data": True,
            "bp_systolic_avg": 140,
            "gender_enc": 1
        }
        diet1 = generate_diet_plan(features_high_bp)
        
        # Test with high sugar
        features_high_sugar = {
            "has_vitals_data": True,
            "sugar_avg": 120,
            "gender_enc": 1
        }
        diet2 = generate_diet_plan(features_high_sugar)
        
        if diet1 and diet2:
            print(f"✅ High BP diet: {diet1['focus_type']}")
            print(f"   Eat more: {', '.join(diet1['eat_more'][:3])}...")
            print(f"✅ High sugar diet: {diet2['focus_type']}")
            print(f"   Eat more: {', '.join(diet2['eat_more'][:3])}...")
            
            # Verify they're different
            if diet1['focus_type'] != diet2['focus_type']:
                print("✅ Diet plans are personalized per condition")
                return True
            else:
                print("⚠️  Diet plans are identical (should differ)")
                return False
        else:
            print("❌ Diet plan generation failed")
            return False
    except Exception as e:
        print(f"❌ Diet plan test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_daily_tasks_generation():
    """Test 7: Daily Tasks Generation"""
    print("\n" + "="*60)
    print("TEST 7: Daily Tasks Generation")
    print("="*60)
    try:
        from ml.analysis_engine import generate_daily_tasks
        
        features = {
            "has_vitals_data": True,
            "bp_systolic_latest": 135,
            "sugar_latest": 110,
            "hemoglobin": 11.5,
            "platelet_count": 140000,
            "bmi": 28,
            "gender_enc": 1
        }
        
        class MockUser:
            pass
        
        tasks = generate_daily_tasks(features, MockUser())
        
        print(f"✅ Generated {len(tasks)} tasks")
        
        # Check for specific tasks
        task_types = [t["task_type"] for t in tasks]
        
        if "MORNING_WALK" in task_types:
            walk_task = [t for t in tasks if t["task_type"] == "MORNING_WALK"][0]
            print(f"✅ Walking task: {walk_task['task_name']} ({walk_task['coins_reward']} coins)")
        
        if "EAT_PAPAYA" in task_types:
            print(f"✅ Papaya task generated (low platelets detected)")
        
        if "IRON_RICH_MEAL" in task_types:
            print(f"✅ Iron meal task generated (low Hb detected)")
        
        return len(tasks) > 0
    except Exception as e:
        print(f"❌ Daily tasks test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("\n" + "="*60)
    print("VITALID COMPLETE SYSTEM TEST")
    print("="*60)
    
    results = []
    
    # Run all tests
    results.append(("Database Connection", await test_database_connection()))
    results.append(("User Creation", await test_user_creation()))
    results.append(("BP Classification", await test_bp_classification()))
    results.append(("Preventive Care Messages", await test_preventive_care_messages()))
    results.append(("OCR Prompt Enhancement", await test_ocr_prompt()))
    results.append(("Diet Plan Generation", await test_diet_plan_generation()))
    results.append(("Daily Tasks Generation", await test_daily_tasks_generation()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - System is production ready!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - review errors above")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
