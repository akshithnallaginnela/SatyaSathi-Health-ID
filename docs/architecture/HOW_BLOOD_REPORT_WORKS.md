# 🩸 How Blood Report Upload Works

## Quick Summary

When you upload a blood report:
1. **File is sent** to backend API
2. **Gemini Vision AI** extracts 40+ health values (Hb, Platelets, WBC, Glucose, etc.)
3. **ML Analysis** runs with ALL your data (BP, sugar, blood report)
4. **Generates**:
   - Preventive care for blood markers (e.g., "Hb 12.5 — eat iron-rich foods")
   - Daily tasks (e.g., "Eat papaya" for low platelets)
   - Updated diet plan
5. **Dashboard updates** automatically with new insights

**Time**: 7-13 seconds total

---

## Step-by-Step Flow

### 1. Upload (Frontend)
- User clicks "Upload Report" in Vitals screen
- Selects JPG/PNG/PDF file
- File sent to: `POST /api/reports/analyze`

### 2. Validation (Backend)
- Check file size (<10MB)
- Check format (JPG/PNG/PDF only)
- Save to `backend/uploads/` folder

### 3. OCR Extraction (Gemini AI)
- Sends image to Gemini Vision API
- Enhanced prompt recognizes ALL lab formats:
  - Drlogy, SRN, Apollo, Bio Rad, Healthians, Redcliffe, etc.
- Handles unit conversions:
  - "150 K" → 150000 (platelets)
  - "4.84 th/cumm" → 4840 (WBC)
  - "1.5 Lakhs" → 150000
- Extracts 40+ values:
  - Hemoglobin, RBC, WBC, Platelets
  - Glucose, HbA1c
  - Creatinine, Urea
  - SGPT, SGOT
  - Cholesterol, HDL, LDL
  - TSH, Vitamin D, Vitamin B12
  - And more...

### 4. Save to Database
- Creates `BloodReport` record with all extracted values
- Updates `UserDataStatus` (has_report = true)

### 5. ML Analysis
**Collects ALL your data**:
- User profile (age, gender, BMI)
- BP readings (last 30)
- Sugar readings (last 30)
- Blood report (just uploaded)

**Calculates**:
- Health Index (0-100 score)
- Preventive care for each marker
- Daily tasks based on report
- Personalized diet plan

### 6. Generate Preventive Care
**Example for Drlogy Report (Hb 12.5, Platelets 150000)**:

```
Hemoglobin (👀 Watch):
  Status: "Hemoglobin 12.5 g/dL — Mildly low"
  Message: "Hemoglobin is slightly low. Daily iron-rich meals 
            with citrus fruit can restore it in 6-8 weeks."
  Action: "Daily iron-rich meal: spinach dal, rajma, or eggs"

Platelets (👀 Watch):
  Status: "Platelets 150,000/cumm — Mildly low"
  Message: "Platelets are slightly low. Eat fresh papaya daily 
            and retest in 2-3 weeks to confirm the trend."
  Action: "Eat fresh papaya daily"
```

### 7. Generate Daily Tasks
**Example tasks**:
1. Walk 7,000 steps (18 coins) - based on BP + BMI
2. Eat iron-rich food today (0 coins) - based on low Hb
3. Eat fresh papaya today (0 coins) - based on low platelets
4. Drink 8 glasses of water (10 coins) - general wellness

### 8. Generate Diet Plan
**Example for low Hb**:
- **Focus**: iron_boost
- **Reason**: "Building up your hemoglobin (12.5 g/dL)"
- **Eat More**: Spinach, palak, methi, rajma, chana, masoor dal, jaggery, pomegranate, beetroot
- **Reduce**: Tea right after meals (blocks iron)

### 9. Save to Database
- Deletes old preventive care
- Inserts new preventive care (3-5 items)
- Deletes old incomplete tasks
- Inserts new tasks (3-5 tasks)
- Deletes old diet plan
- Inserts new diet plan

### 10. Return Response
Backend sends to frontend:
- Extracted values (all OCR data)
- Health index (74)
- Preventive care items (3-5)
- Daily tasks (3-5)
- Diet plan

### 11. Dashboard Updates
- Frontend receives response
- Triggers dashboard refresh
- User sees:
  - ✅ New preventive care cards for blood markers
  - ✅ New daily tasks based on report
  - ✅ Updated diet plan
  - ✅ Updated health index score

---

## Example: Drlogy Report

### Input Image
```
DRLOGY PATHOLOGY LAB
Patient: Yash M. Patel, 21M

HEMOGLOBIN: 12.5 (Low) - 13.0-17.0 g/dL
RBC COUNT: 5.2 - 4.5-5.5 mill/cumm
WBC COUNT: 9000 - 4000-11000 cumm
PLATELET COUNT: 150000 (Borderline) - 150000-410000 cumm
```

### OCR Extracts
```json
{
  "hemoglobin": 12.5,
  "rbc_count": 5.2,
  "wbc_count": 9000,
  "platelet_count": 150000,
  "lab_name": "DRLOGY PATHOLOGY LAB"
}
```

### Dashboard Shows
**Preventive Care**:
- Hemoglobin 12.5 g/dL — Mildly low (👀 Watch)
- Platelets 150,000/cumm — Mildly low (👀 Watch)

**Daily Tasks**:
- Eat iron-rich food today
- Eat fresh papaya today
- Walk 7,000 steps
- Drink 8 glasses of water

**Diet Plan**:
- Eat More: Spinach, rajma, pomegranate, beetroot
- Reduce: Tea after meals

---

## Supported Lab Formats

✅ **Drlogy Pathology Lab** (Mumbai, Bihar)
- Uses "Ok", "Low", "High", "Borderline" labels
- Example: "12.5 Low 13.0-17.0 g/dL"

✅ **SRN Diagnostics** (Indore)
- Uses "10^3/μL" for WBC/Platelets
- Example: "150 10^3/μL" = 150000

✅ **Apollo Diagnostics** (Shri Ram Hospital)
- Biochemistry format
- Example: "GLUCOSE, RANDOM: 105 mg/dL"

✅ **Bio Rad Lab**
- Uses "/cumm" units
- Includes peripheral smear findings

✅ **Healthians**
- Uses "th/cumm" for WBC
- Example: "4.84 th/cumm" = 4840

✅ **Redcliffe Labs**
- Uses "10^6/μl" for RBC
- Example: "4.6 10^6/μl" = 4.6 million

✅ **Metropolis, Thyrocare, SRL, Dr. Lal PathLabs**
- Standard formats supported

---

## What Gets Extracted (40+ Markers)

### CBC - RBC Parameters
- Hemoglobin (Hb)
- RBC Count
- PCV / HCT / Hematocrit
- MCV, MCH, MCHC
- RDW, RDW-SD
- MPV

### CBC - WBC Parameters
- WBC Count / TLC
- Neutrophils / Polymorphs (%)
- Lymphocytes (%)
- Monocytes (%)
- Eosinophils (%)
- Basophils (%)
- Absolute counts for each

### Platelets
- Platelet Count
- P-LCR

### Blood Sugar
- Fasting Glucose
- Random Glucose
- HbA1c

### Kidney Function
- Creatinine
- Urea
- Uric Acid
- eGFR

### Liver Function
- SGPT / ALT
- SGOT / AST
- Bilirubin (Total, Direct)
- Alkaline Phosphatase
- Albumin
- Total Protein

### Lipid Profile
- Total Cholesterol
- HDL
- LDL
- Triglycerides
- VLDL

### Thyroid
- TSH
- T3
- T4

### Vitamins & Minerals
- Vitamin D
- Vitamin B12
- Iron
- Ferritin
- Calcium
- Sodium
- Potassium

### Other
- Peripheral Smear findings (text)
- Lab name
- Report date
- Lab interpretation

---

## Timing Breakdown

1. File upload: ~1-2 seconds
2. OCR extraction: ~5-10 seconds (Gemini API call)
3. ML analysis: ~500-800ms
4. Database save: ~100-200ms
5. Frontend refresh: ~200-300ms

**Total**: 7-13 seconds from upload to dashboard update

---

## Troubleshooting

### OCR Fails
**Check**:
1. GEMINI_API_KEY in `backend/.env`
2. Backend console for errors
3. File format (JPG/PNG/PDF only)
4. File size (<10MB)

**Fix**:
- Verify API key is valid
- Check backend logs: "📋 OCR extracted X values"
- Try different image (clearer, higher resolution)

### No Preventive Care
**Causes**:
1. OCR extracted 0 values
2. No other vitals logged (need BP or sugar first)
3. Database not updated

**Fix**:
- Check backend logs for extraction count
- Log BP or sugar reading first
- Run: `cd backend && python force_reanalysis.py`

### Tasks Not Showing
**Causes**:
1. Analysis didn't run
2. Database error
3. Frontend not refreshing

**Fix**:
- Check backend logs for "🔬 Analysis: health_index=..."
- Hard refresh browser (Ctrl+Shift+R)
- Check database: `cd backend && python test_complete_system.py`

---

## Test It Now!

1. **Start backend**:
   ```bash
   cd backend
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Upload report**:
   - Go to http://localhost:3000
   - Click "Vitals" tab
   - Click "Upload Report"
   - Select any of your 7 sample reports
   - Wait 7-13 seconds

4. **Check dashboard**:
   - Go to "Dashboard" tab
   - Scroll to "Preventive Care" section
   - Should see cards for blood markers
   - Should see new daily tasks
   - Should see updated diet plan

---

**The system is ready! Upload a report and watch it work! 🎉**
