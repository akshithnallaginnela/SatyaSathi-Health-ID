# 🚀 Quick Reference - Report Upload System

## 📋 Key Changes at a Glance

### Problem → Solution
| Issue | Root Cause | Fix | File |
|-------|-----------|-----|------|
| Tasks not updating | Generated once per day | Delete incomplete tasks on new report | `ml.py` |
| No diet plans | Predicted but not stored | Created diet plan builder | `ml.py` |
| No diet API | Missing endpoint | New `/api/diet/plan` | `diet.py` |

---

## 🔌 API Quick Reference

### Upload Report & Get Analysis
```bash
POST /api/ml/analyze-report
Headers: Authorization: Bearer {token}
Body: multipart/form-data
  - file: image file
  - report_type: "blood_test" | "blood_sugar_report"

Response:
{
  "ml_analysis": { "risk_level": "moderate", "diet_focus": "iron_rich" },
  "diet_plan": { "breakfast": [...], "lunch": [...] },
  "tasks_updated": 2
}
```

### Get Latest Diet Plan
```bash
GET /api/diet/plan
Headers: Authorization: Bearer {token}

Response:
{
  "has_plan": true,
  "diet_plan": {
    "focus": "iron_rich",
    "breakfast": ["Spinach paratha with curd", ...],
    "lunch": ["Brown rice with dal palak", ...],
    "dinner": ["Vegetable khichdi with spinach", ...],
    "snacks": ["Roasted peanuts and jaggery", ...],
    "avoid": ["Tea/coffee immediately after meals", ...],
    "hydration": "Drink 8-10 glasses of water daily",
    "note": "💡 Personalized suggestion..."
  }
}
```

### Get Today's Tasks
```bash
GET /api/tasks/today
Headers: Authorization: Bearer {token}

Response:
[
  {
    "id": "task-123",
    "task_type": "IRON_DIET",
    "task_name": "Eat Iron-Rich Meal (Spinach/Lentils)",
    "coins_reward": 25,
    "completed": false,
    "time_slot": "afternoon"
  }
]
```

### Get Dashboard Summary
```bash
GET /api/dashboard/summary
Headers: Authorization: Bearer {token}

Response:
{
  "preventive_analytics": {
    "risk_level": "moderate",
    "summary": "Some findings indicate...",
    "positive_precautions": [...],
    "diet_plan": { ... }
  },
  "todays_tasks": [...]
}
```

---

## 🔄 Data Flow

```
┌─────────────────┐
│ Upload Report   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ OCR Extraction  │ (Gemini 1.5 Flash)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ML Risk Analysis│ (Rule-based + Trained Model)
└────────┬────────┘
         │
         ├──────────────────┬──────────────────┬──────────────────┐
         ▼                  ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Delete Old Tasks│ │ Generate Diet   │ │ Build Precautions│ │ Store Report    │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                  │                  │                  │
         ▼                  ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Create New Tasks│ │ Store in Report │ │ Store in Report │ │ Return Response │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 🎯 Diet Plan Types

| Focus | Condition | Key Foods | Avoid |
|-------|-----------|-----------|-------|
| `iron_rich` | Anemia | Spinach, lentils, jaggery, dates | Tea/coffee after meals |
| `diabetic_friendly` | High glucose | Oats, vegetables, brown rice | White rice, sweets, fried foods |
| `iron_and_low_sugar` | Both | Iron foods + low GI | Tea + sugary foods |
| `balanced` | Normal | Balanced meals | Excessive fried/processed |

---

## 🧪 Testing Checklist

```bash
# 1. Upload first report (anemia)
curl -X POST .../analyze-report -F "file=@anemia.png"
# ✅ Check: tasks_updated > 0

# 2. Get tasks
curl -X GET .../tasks/today
# ✅ Check: IRON_DIET, VITAMIN_C tasks

# 3. Complete one task
curl -X POST .../tasks/{id}/complete
# ✅ Check: completed = true

# 4. Upload second report (diabetes)
curl -X POST .../analyze-report -F "file=@diabetes.png"
# ✅ Check: tasks_updated > 0

# 5. Get tasks again
curl -X GET .../tasks/today
# ✅ Check: Completed task still there
# ✅ Check: Old incomplete tasks gone
# ✅ Check: New diabetes tasks added

# 6. Get diet plan
curl -X GET .../diet/plan
# ✅ Check: focus = "diabetic_friendly"
```

---

## 🔧 Code Snippets

### Frontend: Upload Report
```typescript
async function uploadReport(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('report_type', 'blood_test');
  
  const response = await fetch('/api/ml/analyze-report', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  
  const data = await response.json();
  console.log(`${data.tasks_updated} tasks updated!`);
  return data;
}
```

### Frontend: Display Diet Plan
```typescript
async function showDietPlan() {
  const response = await fetch('/api/diet/plan', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const { diet_plan } = await response.json();
  
  return (
    <div>
      <h3>Breakfast</h3>
      <ul>{diet_plan.breakfast.map(item => <li>{item}</li>)}</ul>
      
      <h3>Lunch</h3>
      <ul>{diet_plan.lunch.map(item => <li>{item}</li>)}</ul>
      
      <h3>Avoid</h3>
      <ul>{diet_plan.avoid.map(item => <li>{item}</li>)}</ul>
    </div>
  );
}
```

### Backend: Add Custom Diet Plan
```python
def _build_diet_plan(diet_focus: str, risk_level: str) -> dict:
    plan = {
        "focus": diet_focus,
        "breakfast": ["Custom meal 1", "Custom meal 2"],
        "lunch": [...],
        "dinner": [...],
        "snacks": [...],
        "avoid": [...],
        "hydration": "Drink 8-10 glasses of water daily",
        "note": "Custom note"
    }
    return plan
```

---

## 🐛 Common Issues

### Tasks not updating
```python
# Check if deletion happened
await db.execute(
    delete(DailyTask).where(
        and_(
            DailyTask.user_id == user_id,
            DailyTask.task_date == today,
            DailyTask.completed == False  # Only incomplete tasks
        )
    )
)
```

### Diet plan is null
```python
# Ensure diet_plan is added to report
report.extracted_values["diet_plan"] = _build_diet_plan(
    ml_result.get("diet_focus", "balanced"),
    ml_result.get("risk_level", "low")
)
```

### Old reports missing diet plans
```bash
# Run migration script
cd backend
python migrate_diet_plans.py
```

---

## 📊 Database Schema

### Report.extracted_values (JSON)
```json
{
  "ocr_data": { ... },
  "ml_analysis": {
    "risk_level": "moderate",
    "diet_focus": "iron_rich",
    "flags": [...]
  },
  "positive_precautions": [...],
  "diet_plan": {
    "focus": "iron_rich",
    "breakfast": [...],
    "lunch": [...],
    "dinner": [...],
    "snacks": [...],
    "avoid": [...],
    "hydration": "...",
    "note": "..."
  }
}
```

---

## 🎯 Key Functions

| Function | Location | Purpose |
|----------|----------|---------|
| `_build_diet_plan()` | `ml.py` | Generate meal suggestions |
| `_build_positive_precautions()` | `ml.py` | Generate health tips |
| `_tasks_from_model_predictions()` | `ml.py` | Convert ML predictions to tasks |
| `analyze()` | `report_analyzer.py` | ML risk assessment |
| `predict_from_ocr()` | `realistic_predictor.py` | Trained model inference |

---

## 📝 Environment Variables

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key
JWT_SECRET=your_jwt_secret

# Optional
RISK_MODEL_PATH=backend/ml/models/risk_model.joblib
```

---

## 🚀 Deployment

```bash
# 1. Pull latest code
git pull origin main

# 2. Install dependencies (if any new)
pip install -r backend/requirements.txt

# 3. Run migration (optional, for existing reports)
cd backend
python migrate_diet_plans.py

# 4. Restart server
# Backend will auto-create tables on startup
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📚 Documentation Files

- `EXECUTIVE_SUMMARY.md` - High-level overview
- `REPORT_UPLOAD_FIXES.md` - Detailed technical docs
- `TESTING_GUIDE.md` - Step-by-step testing
- `QUICK_REFERENCE.md` - This file

---

**Last Updated**: January 2025
**Version**: 2.0.0
