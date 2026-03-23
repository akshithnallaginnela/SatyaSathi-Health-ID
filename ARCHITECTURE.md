# 🏗️ System Architecture - Report Upload Flow

## 📊 Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER UPLOADS HEALTH REPORT                       │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    POST /api/ml/analyze-report                           │
│                    (backend/routers/ml.py)                               │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         STEP 1: OCR EXTRACTION                           │
│                    (services/ocr_service.py)                             │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Gemini 1.5 Flash Vision API                                     │   │
│  │  • Extract patient name, date, doctor                            │   │
│  │  • Extract lab results (hemoglobin, glucose, etc.)               │   │
│  │  • Extract key findings                                          │   │
│  │  • Extract medications                                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  Output: ocr_data = {                                                    │
│    "document_type": "Blood Test Report",                                 │
│    "lab_results": { "hemoglobin": "10.5 g/dL", ... },                   │
│    "key_findings": ["Low hemoglobin", ...],                              │
│    "medications": [...]                                                  │
│  }                                                                        │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      STEP 2: ML RISK ANALYSIS                            │
│                    (ml/report_analyzer.py)                               │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Rule-Based Analysis                                             │   │
│  │  • Scan for high-risk keywords (DKA, heart attack, etc.)         │   │
│  │  • Scan for moderate-risk keywords (prediabetes, etc.)           │   │
│  │  • Check numeric values (hemoglobin < 7, glucose > 250)          │   │
│  │  • Calculate risk score                                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Trained Model Analysis (if available)                           │   │
│  │  • Load XGBoost model                                            │   │
│  │  • Predict risk level                                            │   │
│  │  • Get confidence score                                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  Output: ml_result = {                                                   │
│    "risk_level": "moderate",                                             │
│    "flags": ["Moderate finding: Low Hemoglobin"],                        │
│    "confidence": 0.85,                                                   │
│    "diet_focus": "iron_rich"                                             │
│  }                                                                        │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    STEP 3: DELETE OLD INCOMPLETE TASKS                   │
│                    (routers/ml.py - NEW!)                                │
│                                                                           │
│  DELETE FROM daily_tasks                                                 │
│  WHERE user_id = current_user                                            │
│    AND task_date = today                                                 │
│    AND completed = FALSE  ← Only incomplete tasks!                       │
│                                                                           │
│  ✅ Completed tasks are PRESERVED                                        │
│  ❌ Old incomplete tasks are DELETED                                     │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    STEP 4: GENERATE NEW TASKS                            │
│                    (routers/ml.py)                                       │
│                                                                           │
│  Based on risk_level and report_type:                                    │
│                                                                           │
│  IF anemia detected:                                                     │
│    ✅ IRON_DIET: "Eat Iron-Rich Meal (Spinach/Lentils)" - 25 coins      │
│    ✅ VITAMIN_C: "Take Vitamin C (Lemon/Orange)" - 15 coins             │
│                                                                           │
│  IF diabetes detected:                                                   │
│    ✅ POST_MEAL_WALK: "15 Min Post-Meal Walk" - 20 coins                │
│    ✅ AVOID_SUGAR: "Zero Added Sugar Today" - 25 coins                  │
│                                                                           │
│  IF normal/low risk:                                                     │
│    ✅ WATER_INTAKE: "Drink 8 Glasses Water" - 15 coins                  │
│    ✅ DEEP_BREATHING: "5 Min Deep Breathing" - 15 coins                 │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    STEP 5: BUILD DIET PLAN                               │
│                    (routers/ml.py - NEW!)                                │
│                                                                           │
│  _build_diet_plan(diet_focus, risk_level)                               │
│                                                                           │
│  IF diet_focus == "iron_rich":                                           │
│    breakfast: ["Spinach paratha", "Ragi porridge", ...]                 │
│    lunch: ["Dal palak with rice", "Rajma curry", ...]                   │
│    dinner: ["Vegetable khichdi", "Chana masala", ...]                   │
│    snacks: ["Peanuts and jaggery", "Dates", ...]                        │
│    avoid: ["Tea/coffee after meals", ...]                               │
│                                                                           │
│  IF diet_focus == "diabetic_friendly":                                   │
│    breakfast: ["Oats upma", "Moong dal chilla", ...]                    │
│    lunch: ["Brown rice with dal", "Quinoa", ...]                        │
│    avoid: ["White rice", "Sweets", "Fried foods", ...]                  │
│                                                                           │
│  Output: diet_plan = { focus, breakfast, lunch, dinner, snacks, avoid } │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    STEP 6: BUILD PRECAUTIONS                             │
│                    (routers/ml.py)                                       │
│                                                                           │
│  _build_positive_precautions(risk_level, report_type, flags)            │
│                                                                           │
│  IF anemia:                                                              │
│    • "Increase dietary iron: spinach, nuts, lentils, jaggery"           │
│    • "Pair iron foods with Vitamin C for better absorption"             │
│    • "Avoid tea/coffee immediately after meals"                         │
│                                                                           │
│  IF diabetes:                                                            │
│    • "Add 15-20 minute post-meal walk"                                  │
│    • "Use high-fiber meals, reduce refined sugar"                       │
│                                                                           │
│  IF high risk:                                                           │
│    • "Book doctor follow-up this week" (added first)                    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    STEP 7: STORE REPORT                                  │
│                    (models/report.py)                                    │
│                                                                           │
│  Report.extracted_values = {                                             │
│    "ocr_data": { ... },                                                  │
│    "ml_analysis": {                                                      │
│      "risk_level": "moderate",                                           │
│      "flags": [...],                                                     │
│      "diet_focus": "iron_rich"                                           │
│    },                                                                    │
│    "positive_precautions": [...],                                        │
│    "diet_plan": {                                                        │
│      "focus": "iron_rich",                                               │
│      "breakfast": [...],                                                 │
│      "lunch": [...],                                                     │
│      "dinner": [...],                                                    │
│      "snacks": [...],                                                    │
│      "avoid": [...]                                                      │
│    }                                                                     │
│  }                                                                        │
│                                                                           │
│  Save to database ✅                                                     │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    STEP 8: RETURN RESPONSE                               │
│                                                                           │
│  {                                                                        │
│    "message": "Report analyzed successfully.",                           │
│    "report_id": "abc-123",                                               │
│    "ml_analysis": { ... },                                               │
│    "diet_plan": { ... },                                                 │
│    "positive_precautions": [...],                                        │
│    "tasks_updated": 2  ← NEW!                                           │
│  }                                                                        │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER SEES RESULTS                                │
│                                                                           │
│  ✅ Updated tasks in task list                                          │
│  ✅ Personalized diet plan                                              │
│  ✅ Health precautions                                                  │
│  ✅ Risk level and summary                                              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Task Update Flow (Detailed)

```
BEFORE NEW REPORT UPLOAD:
┌─────────────────────────────────────────────────────────────────────────┐
│  Today's Tasks (from first report - Anemia)                              │
│                                                                           │
│  ✅ IRON_DIET: "Eat Iron-Rich Meal" (completed by user)                 │
│  ⏳ VITAMIN_C: "Take Vitamin C" (incomplete)                            │
│  ⏳ MORNING_WALK: "20 Min Walk" (incomplete)                            │
└─────────────────────────────────────────────────────────────────────────┘

                                 │
                                 │ User uploads new report (Diabetes)
                                 ▼

STEP 1: DELETE INCOMPLETE TASKS
┌─────────────────────────────────────────────────────────────────────────┐
│  DELETE FROM daily_tasks                                                 │
│  WHERE completed = FALSE                                                 │
│                                                                           │
│  ❌ VITAMIN_C deleted                                                    │
│  ❌ MORNING_WALK deleted                                                 │
│  ✅ IRON_DIET preserved (was completed)                                 │
└─────────────────────────────────────────────────────────────────────────┘

                                 │
                                 ▼

STEP 2: CREATE NEW TASKS
┌─────────────────────────────────────────────────────────────────────────┐
│  Based on diabetes report:                                               │
│                                                                           │
│  ➕ POST_MEAL_WALK: "15 Min Post-Meal Walk" (new)                       │
│  ➕ AVOID_SUGAR: "Zero Added Sugar Today" (new)                         │
└─────────────────────────────────────────────────────────────────────────┘

                                 │
                                 ▼

AFTER NEW REPORT UPLOAD:
┌─────────────────────────────────────────────────────────────────────────┐
│  Today's Tasks (updated for Diabetes)                                    │
│                                                                           │
│  ✅ IRON_DIET: "Eat Iron-Rich Meal" (preserved - was completed)         │
│  ⏳ POST_MEAL_WALK: "15 Min Post-Meal Walk" (new - for diabetes)       │
│  ⏳ AVOID_SUGAR: "Zero Added Sugar Today" (new - for diabetes)         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🍽️ Diet Plan Generation Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ML Analysis Output                                    │
│                    diet_focus: "iron_rich"                               │
│                    risk_level: "moderate"                                │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              _build_diet_plan("iron_rich", "moderate")                   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  IF diet_focus == "iron_rich":                                           │
│                                                                           │
│    Breakfast Options:                                                    │
│    • Spinach paratha with curd                                           │
│    • Ragi porridge with jaggery                                          │
│    • Moong dal chilla with mint chutney                                  │
│                                                                           │
│    Lunch Options:                                                        │
│    • Brown rice with dal palak and beetroot salad                        │
│    • Roti with rajma curry and cucumber raita                            │
│    • Quinoa pulao with mixed vegetables                                  │
│                                                                           │
│    Dinner Options:                                                       │
│    • Vegetable khichdi with spinach                                      │
│    • Roti with chana masala and green salad                              │
│    • Millet roti with palak paneer                                       │
│                                                                           │
│    Snacks:                                                               │
│    • Roasted peanuts and jaggery                                         │
│    • Dates and almonds (4-5 pieces)                                      │
│    • Beetroot and carrot juice                                           │
│                                                                           │
│    Avoid:                                                                │
│    • Tea/coffee immediately after meals                                  │
│    • Excessive calcium supplements with iron-rich meals                  │
│                                                                           │
│    Hydration: "Drink 8-10 glasses of water daily"                        │
│    Note: "💡 Personalized suggestion. Adjust portions..."               │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Store in Report.extracted_values                      │
│                    Return to user                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 API Endpoint Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                         │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │ Upload Report│ │  Get Tasks   │ │  Get Diet    │
        │              │ │              │ │    Plan      │
        └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
               │                │                │
               ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         BACKEND ROUTERS                                  │
│                                                                           │
│  POST /api/ml/analyze-report                                             │
│  ├─→ OCR Service (Gemini)                                                │
│  ├─→ ML Analysis (report_analyzer.py)                                    │
│  ├─→ Delete Old Tasks                                                    │
│  ├─→ Generate New Tasks                                                  │
│  ├─→ Build Diet Plan                                                     │
│  └─→ Store Report                                                        │
│                                                                           │
│  GET /api/tasks/today                                                    │
│  └─→ Fetch today's tasks from database                                  │
│                                                                           │
│  GET /api/diet/plan                                                      │
│  └─→ Fetch latest report's diet plan                                    │
│                                                                           │
│  GET /api/dashboard/summary                                              │
│  ├─→ Fetch latest report                                                 │
│  ├─→ Fetch today's tasks                                                 │
│  ├─→ Calculate wellness score                                            │
│  └─→ Return complete dashboard data                                     │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATABASE (SQLite)                                │
│                                                                           │
│  reports                                                                 │
│  ├─ id                                                                   │
│  ├─ user_id                                                              │
│  ├─ report_type                                                          │
│  ├─ extracted_values (JSON)                                              │
│  │   ├─ ocr_data                                                         │
│  │   ├─ ml_analysis                                                      │
│  │   ├─ positive_precautions                                             │
│  │   └─ diet_plan ← NEW!                                                │
│  └─ uploaded_at                                                          │
│                                                                           │
│  daily_tasks                                                             │
│  ├─ id                                                                   │
│  ├─ user_id                                                              │
│  ├─ task_type                                                            │
│  ├─ task_name                                                            │
│  ├─ coins_reward                                                         │
│  ├─ task_date                                                            │
│  ├─ completed                                                            │
│  └─ completed_at                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Security Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                                     │
│                    Authorization: Bearer {JWT_TOKEN}                     │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    JWT Authentication Middleware                         │
│                    (security/jwt_handler.py)                             │
│                                                                           │
│  1. Extract token from Authorization header                              │
│  2. Verify token signature                                               │
│  3. Check token expiration                                               │
│  4. Extract user_id from token                                           │
│  5. Pass user_id to endpoint                                             │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ENDPOINT HANDLER                                 │
│                    (user_id: str = Depends(get_current_user_id))        │
│                                                                           │
│  • All queries filtered by user_id                                       │
│  • Users can only access their own data                                  │
│  • No cross-user data leakage                                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

**This architecture ensures:**
- ✅ Dynamic task updates based on latest reports
- ✅ Personalized diet plans for each condition
- ✅ Secure, user-specific data access
- ✅ Efficient database queries
- ✅ Scalable and maintainable code structure
