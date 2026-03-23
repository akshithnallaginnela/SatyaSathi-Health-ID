# 🧪 Testing Guide - Report Upload Fixes

## Prerequisites

1. Backend running on `http://localhost:8000`
2. Frontend running on `http://localhost:3000` or `http://localhost:5173`
3. Valid JWT token (login first)
4. Test health report images

---

## 🔍 Test Scenario 1: First Report Upload (Anemia)

### Step 1: Upload Anemia Report

**API Call**:
```bash
curl -X POST http://localhost:8000/api/ml/analyze-report \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_anemia_report.png" \
  -F "report_type=blood_test"
```

**Expected Response**:
```json
{
  "message": "Report analyzed successfully.",
  "report_id": "abc-123",
  "ml_analysis": {
    "risk_level": "moderate",
    "flags": ["Moderate finding: Low Hemoglobin"],
    "diet_focus": "iron_rich"
  },
  "diet_plan": {
    "focus": "iron_rich",
    "breakfast": ["Spinach paratha with curd", ...],
    "lunch": ["Brown rice with dal palak and beetroot salad", ...],
    "avoid": ["Tea/coffee immediately after meals", ...]
  },
  "tasks_updated": 2
}
```

### Step 2: Check Today's Tasks

**API Call**:
```bash
curl -X GET http://localhost:8000/api/tasks/today \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Tasks**:
```json
[
  {
    "task_type": "IRON_DIET",
    "task_name": "Eat Iron-Rich Meal (Spinach/Lentils)",
    "coins_reward": 25,
    "completed": false
  },
  {
    "task_type": "VITAMIN_C",
    "task_name": "Take Vitamin C (Lemon/Orange)",
    "coins_reward": 15,
    "completed": false
  }
]
```

### Step 3: Check Dashboard

**API Call**:
```bash
curl -X GET http://localhost:8000/api/dashboard/summary \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**:
```json
{
  "preventive_analytics": {
    "risk_level": "moderate",
    "summary": "Some findings indicate health risks...",
    "positive_precautions": [
      "Increase dietary iron: focus on spinach, nuts, lentils, and jaggery.",
      "Pair iron-rich foods with Vitamin C (like lemon/orange) for better absorption."
    ],
    "diet_plan": {
      "focus": "iron_rich",
      ...
    }
  }
}
```

### Step 4: Get Diet Plan

**API Call**:
```bash
curl -X GET http://localhost:8000/api/diet/plan \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**:
```json
{
  "has_plan": true,
  "diet_plan": {
    "focus": "iron_rich",
    "breakfast": [
      "Spinach paratha with curd",
      "Ragi porridge with jaggery",
      "Moong dal chilla with mint chutney"
    ],
    "snacks": [
      "Roasted peanuts and jaggery",
      "Dates and almonds (4-5 pieces)"
    ]
  },
  "risk_level": "moderate"
}
```

✅ **Test 1 PASSED** if:
- Report uploaded successfully
- Tasks show iron-rich diet recommendations
- Dashboard shows anemia precautions
- Diet plan focuses on iron-rich foods

---

## 🔍 Test Scenario 2: Second Report Upload (Diabetes)

### Step 1: Complete One Task (Optional)

**API Call**:
```bash
curl -X POST http://localhost:8000/api/tasks/{task_id}/complete \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Purpose**: Verify completed tasks are NOT deleted when new report is uploaded.

### Step 2: Upload Diabetes Report

**API Call**:
```bash
curl -X POST http://localhost:8000/api/ml/analyze-report \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_diabetes_report.png" \
  -F "report_type=blood_sugar_report"
```

**Expected Response**:
```json
{
  "message": "Report analyzed successfully.",
  "ml_analysis": {
    "risk_level": "moderate",
    "flags": ["Moderate finding: Glucose Elevated"],
    "diet_focus": "diabetic_friendly"
  },
  "diet_plan": {
    "focus": "diabetic_friendly",
    "breakfast": ["Oats upma with vegetables", ...],
    "avoid": ["White rice, white bread, maida products", ...]
  },
  "tasks_updated": 2
}
```

### Step 3: Check Tasks Again

**API Call**:
```bash
curl -X GET http://localhost:8000/api/tasks/today \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**:
```json
[
  {
    "task_type": "IRON_DIET",
    "task_name": "Eat Iron-Rich Meal (Spinach/Lentils)",
    "completed": true  // ✅ Completed task preserved
  },
  {
    "task_type": "POST_MEAL_WALK",
    "task_name": "15 Min Post-Meal Walk",
    "coins_reward": 20,
    "completed": false  // ✅ NEW task for diabetes
  },
  {
    "task_type": "AVOID_SUGAR",
    "task_name": "Zero Added Sugar Today",
    "coins_reward": 25,
    "completed": false  // ✅ NEW task for diabetes
  }
]
```

**Verify**:
- ❌ Old incomplete anemia tasks (VITAMIN_C) are GONE
- ✅ Completed tasks are PRESERVED
- ✅ New diabetes tasks are ADDED

### Step 4: Check Dashboard

**API Call**:
```bash
curl -X GET http://localhost:8000/api/dashboard/summary \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**:
```json
{
  "preventive_analytics": {
    "risk_level": "moderate",
    "positive_precautions": [
      "Add a 15-20 minute post-meal walk to support steady sugar levels.",
      "Use high-fiber meals and reduce refined sugar portions gradually."
    ],
    "diet_plan": {
      "focus": "diabetic_friendly",  // ✅ Changed from iron_rich
      ...
    }
  }
}
```

### Step 5: Get Diet Plan

**API Call**:
```bash
curl -X GET http://localhost:8000/api/diet/plan \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**:
```json
{
  "diet_plan": {
    "focus": "diabetic_friendly",  // ✅ Updated
    "breakfast": [
      "Oats upma with vegetables",
      "Moong dal chilla with green chutney"
    ],
    "avoid": [
      "White rice, white bread, maida products",
      "Sugary drinks, sweets, and desserts"
    ]
  }
}
```

✅ **Test 2 PASSED** if:
- Old incomplete tasks deleted
- Completed tasks preserved
- New tasks match diabetes condition
- Dashboard shows diabetes precautions
- Diet plan changed to diabetic-friendly

---

## 🔍 Test Scenario 3: Third Report Upload (Normal/Low Risk)

### Step 1: Upload Normal Report

**API Call**:
```bash
curl -X POST http://localhost:8000/api/ml/analyze-report \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_normal_report.png" \
  -F "report_type=blood_test"
```

**Expected Response**:
```json
{
  "ml_analysis": {
    "risk_level": "low",
    "summary": "No significant risk markers found..."
  },
  "diet_plan": {
    "focus": "balanced",
    "breakfast": ["Idli with sambar and coconut chutney", ...]
  },
  "tasks_updated": 2
}
```

### Step 2: Check Tasks

**Expected**:
```json
[
  {
    "task_type": "WATER_INTAKE",
    "task_name": "Drink 8 Glasses Water",
    "completed": false
  },
  {
    "task_type": "DEEP_BREATHING",
    "task_name": "5 Min Deep Breathing",
    "completed": false
  }
]
```

**Verify**: General wellness tasks (no specific medical tasks)

✅ **Test 3 PASSED** if:
- Low risk detected
- General wellness tasks assigned
- Balanced diet plan provided

---

## 🔍 Test Scenario 4: Historical Report Diet Plan

### Step 1: Get All Reports

**API Call**:
```bash
curl -X GET http://localhost:8000/api/reports/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: List of all uploaded reports with IDs

### Step 2: Get Diet Plan for First Report

**API Call**:
```bash
curl -X GET http://localhost:8000/api/diet/plan/{first_report_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**:
```json
{
  "diet_plan": {
    "focus": "iron_rich",  // ✅ Original anemia diet plan
    ...
  },
  "report_id": "abc-123",
  "report_date": "2024-01-15T10:30:00"
}
```

✅ **Test 4 PASSED** if:
- Can retrieve diet plan for any historical report
- Each report has its own diet plan

---

## 🔍 Test Scenario 5: Migration Script

### Step 1: Run Migration

**Command**:
```bash
cd backend
python migrate_diet_plans.py
```

**Expected Output**:
```
🔄 Starting diet plan migration...
============================================================
✅ Added diet plan to report abc-123 (focus: iron_rich, risk: moderate)
✅ Added diet plan to report def-456 (focus: diabetic_friendly, risk: moderate)
✓ Report ghi-789 already has diet plan

============================================================
Migration complete!
  ✅ Updated: 2 reports
  ⏭️  Skipped: 1 reports
============================================================
```

### Step 2: Verify Old Reports Have Diet Plans

**API Call**:
```bash
curl -X GET http://localhost:8000/api/diet/plan/{old_report_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**: Diet plan now exists for old reports

✅ **Test 5 PASSED** if:
- Migration runs without errors
- Old reports now have diet plans

---

## 🎯 Summary Checklist

### Core Functionality
- [ ] First report upload creates appropriate tasks
- [ ] Second report upload deletes old incomplete tasks
- [ ] Second report upload preserves completed tasks
- [ ] Second report upload creates new appropriate tasks
- [ ] Dashboard always shows latest report data
- [ ] Diet plan changes based on report type

### API Endpoints
- [ ] `POST /api/ml/analyze-report` returns diet_plan
- [ ] `GET /api/tasks/today` shows updated tasks
- [ ] `GET /api/dashboard/summary` includes diet_plan
- [ ] `GET /api/diet/plan` returns latest diet plan
- [ ] `GET /api/diet/plan/{report_id}` returns specific diet plan

### Diet Plan Content
- [ ] Iron-rich diet for anemia
- [ ] Diabetic-friendly diet for high glucose
- [ ] Balanced diet for normal reports
- [ ] Includes breakfast, lunch, dinner, snacks
- [ ] Includes foods to avoid
- [ ] Includes hydration recommendations

### Edge Cases
- [ ] Multiple reports same day
- [ ] Report upload with no tasks completed
- [ ] Report upload with all tasks completed
- [ ] User with no reports (diet plan returns null)
- [ ] Invalid report format

---

## 🐛 Troubleshooting

### Issue: Tasks not updating
**Check**:
```bash
# Verify response includes tasks_updated
curl -X POST http://localhost:8000/api/ml/analyze-report ... | jq '.tasks_updated'
# Should return a number > 0
```

### Issue: Diet plan is null
**Check**:
```bash
# Verify report has diet_plan in extracted_values
curl -X GET http://localhost:8000/api/reports/{report_id} \
  -H "Authorization: Bearer YOUR_TOKEN" | jq '.extracted_values.diet_plan'
```

### Issue: Old tasks still showing
**Check**:
```bash
# Verify report upload was successful
# Check database directly
sqlite3 backend/vitalid.db "SELECT * FROM daily_tasks WHERE user_id='USER_ID' AND task_date=date('now');"
```

---

## ✅ Success Criteria

All tests pass if:
1. ✅ Tasks update automatically on new report upload
2. ✅ Completed tasks are preserved
3. ✅ Incomplete tasks are replaced
4. ✅ Dashboard shows latest report data
5. ✅ Diet plans are personalized and stored
6. ✅ Historical reports retain their diet plans
7. ✅ API responses include all new fields

**Your health tracking system is now fully dynamic!** 🎉
