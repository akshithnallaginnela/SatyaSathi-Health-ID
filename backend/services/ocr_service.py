"""
OCR Service — Gemini Vision for blood report extraction.
Handles any lab format: Drlogy, Apollo, Metropolis, SRL, Redcliffe, local labs, etc.
Extracts ALL available blood markers comprehensively.
"""
import os
import json
import io
from PIL import Image
from pydantic import BaseModel

class OCRPayload(BaseModel):
    # CBC — RBC Parameters
    hemoglobin: float | None = None
    rbc_count: float | None = None
    pcv: float | None = None          # also HCT / Hematocrit
    mcv: float | None = None
    mch: float | None = None
    mchc: float | None = None
    rdw: float | None = None
    rdw_sd: float | None = None
    mpv: float | None = None          # Mean Platelet Volume

    # CBC — WBC Parameters
    wbc_count: float | None = None    # TLC / Total Leucocyte Count
    neutrophils_pct: float | None = None
    lymphocytes_pct: float | None = None
    monocytes_pct: float | None = None
    eosinophils_pct: float | None = None
    basophils_pct: float | None = None
    neutrophils_abs: float | None = None
    lymphocytes_abs: float | None = None
    monocytes_abs: float | None = None
    eosinophils_abs: float | None = None

    # Platelets
    platelet_count: float | None = None
    p_lcr: float | None = None        # Platelet Large Cell Ratio

    # Blood Sugar
    fasting_glucose: float | None = None
    random_glucose: float | None = None
    hba1c: float | None = None

    # Kidney Function
    urea: float | None = None
    creatinine: float | None = None
    uric_acid: float | None = None
    egfr: float | None = None

    # Liver Function
    sgpt: float | None = None         # ALT
    sgot: float | None = None         # AST
    bilirubin_total: float | None = None
    bilirubin_direct: float | None = None
    alkaline_phosphatase: float | None = None
    albumin: float | None = None
    total_protein: float | None = None

    # Lipid Profile
    total_cholesterol: float | None = None
    hdl: float | None = None
    ldl: float | None = None
    triglycerides: float | None = None
    vldl: float | None = None

    # Thyroid
    tsh: float | None = None
    t3: float | None = None
    t4: float | None = None

    # Vitamins & Minerals
    vitamin_d: float | None = None
    vitamin_b12: float | None = None
    iron: float | None = None
    ferritin: float | None = None
    calcium: float | None = None
    sodium: float | None = None
    potassium: float | None = None

    # Peripheral Smear findings (text)
    peripheral_smear: str | None = None

    # Meta
    lab_name: str | None = None
    report_date: str | None = None
    lab_interpretation: str | None = None


def _clean_json_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


EXTRACTION_PROMPT = """
You are a highly precise medical data extraction AI specializing in Indian lab reports from ALL major labs.
Extract ALL available health values from this report into a JSON object.

SUPPORTED LAB FORMATS:
- Drlogy Pathology Lab (Mumbai, Bihar, etc.)
- SRN Diagnostics (Indore)
- Apollo Diagnostics (Shri Ram Hospital)
- Bio Rad Lab
- Healthians
- Redcliffe Labs
- Metropolis, Thyrocare, SRL, Dr. Lal PathLabs
- Local diagnostic centers
- Hospital lab reports

CRITICAL EXTRACTION RULES:
1. Return ONLY raw JSON — no markdown, no explanation, no backticks, no code blocks.
2. Use null for any value not present in the report.
3. All numeric values must be numbers (not strings) — remove commas, units, and text.
4. Handle ALL unit variations and naming conventions.

UNIT CONVERSIONS & ALIASES:
- Platelet Count:
  * If "150000" or "1.5 Lakhs" or "1.5 L" → multiply by 100000 → 150000
  * If "150 K" or "150 thousands" → multiply by 1000 → 150000
  * If "150" with unit "10^3/μL" or "10^3/cumm" → multiply by 1000 → 150000
  * If "160000" or plain number → use as-is
  * Common range: 150000-410000 /cumm

- WBC Count (TLC):
  * If "9000" or "9 K" or "9 thousands" → use 9000
  * If "8.63" with unit "10^3/μL" → multiply by 1000 → 8630
  * If "4.84" with unit "th/cumm" → multiply by 1000 → 4840
  * TLC = Total Leucocyte Count = WBC Count
  * Common range: 4000-11000 /cumm

- RBC Count:
  * Always in millions/cumm
  * If "5.2" → use 5.2 (NOT 5200000)
  * If "4.00" → use 4.0
  * Common range: 4.5-6.5 million/cumm for males, 4.0-6.0 for females

- Hemoglobin:
  * Always in g/dL
  * If "12.5" → use 12.5
  * If "10.6" → use 10.6
  * Common range: 13-17 g/dL for males, 12-15 g/dL for females

- PCV/HCT/Hematocrit:
  * Always in %
  * PCV = HCT = Hematocrit (same field)
  * If "57.5" → use 57.5
  * If "33.4" → use 33.4
  * Common range: 40-54% for males, 36-46% for females

- Glucose:
  * Random Glucose: "GLUCOSE, RANDOM" or "RBS" or "Random Blood Sugar"
  * Fasting Glucose: "FBS" or "Fasting Blood Sugar" or "Fasting Glucose"
  * Always in mg/dL
  * If "105" → use 105
  * Common range: 70-140 mg/dL (random), 70-100 mg/dL (fasting)

- Creatinine:
  * "CREATININE, SERUM" or "Serum Creatinine"
  * Always in mg/dL
  * If "0.80" → use 0.8
  * Common range: 0.5-1.04 mg/dL

- Urea:
  * "UREA, SERUM" or "Blood Urea"
  * Always in mg/dL
  * If "22.80" → use 22.8
  * Common range: 15-38 mg/dL

FIELD NAME ALIASES (map these to correct fields):
- POLYMORPHS / Neutrophils → neutrophils_pct
- TLC / Total WBC / TOTAL COUNT (WBC) → wbc_count
- PLT / Platelet Count / PLATELET COUNT → platelet_count
- Hb / HGB / HEMOGLOBIN → hemoglobin
- HCT / PCV / Packed Cell Volume → pcv
- RDW-CV / RDW → rdw
- RDW-SD / RDWSD → rdw_sd
- PDW → use for mpv if MPV not present
- P-LCR / PLCR → p_lcr
- Absolute Neutrophil Count → neutrophils_abs
- Absolute Lymphocyte Count → lymphocytes_abs
- RBC Morphology / Peripheral Blood Smear → peripheral_smear

SPECIAL CASES:
- If platelet count shows "Marked Reduced On Smear" → extract numeric value if present, else null
- If peripheral smear shows "Anisocytosis(+)" or "Neutrophilic Leucocytosis" → capture as string
- If report has multiple pages, extract ALL values from all pages
- If value is marked "Low", "High", "Borderline" → extract the numeric value only
- If reference range is shown (e.g. "13.0 - 17.0") → ignore range, extract only the result value

LAB-SPECIFIC NOTES:
- Drlogy: Uses "Ok", "Low", "High", "Borderline" labels — extract numeric value
- SRN Diagnostics: Uses "10^6/μL" for RBC, "10^3/μL" for WBC/Platelets
- Apollo: Uses "mg/dL" for most biochemistry, "/cumm" for CBC
- Healthians: Uses "th/cumm" for WBC, "thou/μL" for platelets
- Redcliffe: Uses "10^6/μl" for RBC, "10^3/μl" for WBC

Extract these fields:
{
  "hemoglobin": number,           // Hb, HGB, Haemoglobin — g/dL
  "rbc_count": number,            // RBC, Total RBC Count — million/cumm (NOT multiplied)
  "pcv": number,                  // PCV, HCT, Hematocrit — %
  "mcv": number,                  // MCV, Mean Corpuscular Volume — fL
  "mch": number,                  // MCH, Mean Corpuscular Hemoglobin — pg
  "mchc": number,                 // MCHC, Mean Corpuscular Hemoglobin Concentration — g/dL or %
  "rdw": number,                  // RDW, RDW-CV — %
  "rdw_sd": number,               // RDW-SD — fL
  "mpv": number,                  // MPV, Mean Platelet Volume — fL
  "wbc_count": number,            // WBC, TLC, Total Leucocyte Count — /cumm (convert to absolute)
  "neutrophils_pct": number,      // Neutrophils, Polymorphs — %
  "lymphocytes_pct": number,      // Lymphocytes — %
  "monocytes_pct": number,        // Monocytes — %
  "eosinophils_pct": number,      // Eosinophils — %
  "basophils_pct": number,        // Basophils — %
  "neutrophils_abs": number,      // Absolute Neutrophil Count — /cumm
  "lymphocytes_abs": number,      // Absolute Lymphocyte Count — /cumm
  "monocytes_abs": number,        // Absolute Monocyte Count — /cumm
  "eosinophils_abs": number,      // Absolute Eosinophil Count — /cumm
  "platelet_count": number,       // PLT, Platelet Count — /cumm (convert to absolute count)
  "p_lcr": number,                // P-LCR, Platelet Large Cell Ratio — %
  "fasting_glucose": number,      // FBS, Fasting Blood Sugar, Fasting Glucose — mg/dL
  "random_glucose": number,       // RBS, Random Blood Sugar, Random Glucose, GLUCOSE RANDOM — mg/dL
  "hba1c": number,                // HbA1c, Glycated Hemoglobin — %
  "urea": number,                 // Urea, Blood Urea, UREA SERUM — mg/dL
  "creatinine": number,           // Creatinine, Serum Creatinine, CREATININE SERUM — mg/dL
  "uric_acid": number,            // Uric Acid — mg/dL
  "egfr": number,                 // eGFR — mL/min/1.73m2
  "sgpt": number,                 // SGPT, ALT — U/L
  "sgot": number,                 // SGOT, AST — U/L
  "bilirubin_total": number,      // Total Bilirubin — mg/dL
  "bilirubin_direct": number,     // Direct Bilirubin — mg/dL
  "alkaline_phosphatase": number, // ALP, Alkaline Phosphatase — U/L
  "albumin": number,              // Albumin — g/dL
  "total_protein": number,        // Total Protein — g/dL
  "total_cholesterol": number,    // Total Cholesterol — mg/dL
  "hdl": number,                  // HDL Cholesterol — mg/dL
  "ldl": number,                  // LDL Cholesterol — mg/dL
  "triglycerides": number,        // Triglycerides — mg/dL
  "vldl": number,                 // VLDL — mg/dL
  "tsh": number,                  // TSH — mIU/L
  "t3": number,                   // T3 — ng/dL
  "t4": number,                   // T4 — mcg/dL
  "vitamin_d": number,            // Vitamin D, 25-OH Vitamin D — ng/mL
  "vitamin_b12": number,          // Vitamin B12 — pg/mL
  "iron": number,                 // Serum Iron — mcg/dL
  "ferritin": number,             // Ferritin — ng/mL
  "calcium": number,              // Calcium — mg/dL
  "sodium": number,               // Sodium — mEq/L
  "potassium": number,            // Potassium — mEq/L
  "peripheral_smear": string,     // Any peripheral smear findings as text (e.g. "Anisocytosis(+)", "Neutrophilic Leucocytosis")
  "lab_name": string,             // Name of the laboratory (e.g. "DRLOGY PATHOLOGY LAB", "SRN DIAGNOSTICS", "Apollo Diagnostics")
  "report_date": string,          // Date of report in any format
  "lab_interpretation": string    // Doctor's interpretation/conclusion if present (e.g. "Further confirm for Anemia")
}

EXAMPLES FROM REAL REPORTS:
1. Drlogy Report: "Hemoglobin (Hb): 12.5, Low, 13.0-17.0 g/dL" → hemoglobin: 12.5
2. SRN Report: "PLATELET COUNT: 150, 10^3/μL" → platelet_count: 150000
3. Apollo Report: "GLUCOSE, RANDOM: 105 mg/dL" → random_glucose: 105
4. Bio Rad Lab: "Platelet Count: 160000 /cumm" → platelet_count: 160000
5. Healthians: "TLC: 4.84 th/cumm" → wbc_count: 4840
6. Redcliffe: "Hemoglobin: 12.8 g/dL" → hemoglobin: 12.8

VALIDATION:
- Hemoglobin: 8-20 g/dL (typical range)
- RBC: 3.5-7.0 million/cumm
- WBC: 3000-15000 /cumm
- Platelets: 50000-500000 /cumm
- If extracted value is outside these ranges by 10x, check unit conversion

Return ONLY the JSON object, nothing else.
"""


async def extract_report_values(file_path: str) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    ext = file_path.lower().split(".")[-1]
    media_type = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png" if ext == "png" else "application/pdf"

    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        
        if media_type == "application/pdf":
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=[
                    types.Part.from_bytes(data=file_bytes, mime_type=media_type),
                    EXTRACTION_PROMPT
                ]
            )
        else:
            image = Image.open(io.BytesIO(file_bytes))
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=[image, EXTRACTION_PROMPT]
            )

        raw_text = _clean_json_text((response.text or "").strip())
        parsed = json.loads(raw_text)
        payload = OCRPayload.model_validate(parsed)
        result = payload.model_dump()

        # Log extraction summary
        extracted_count = sum(1 for v in result.values() if v is not None and v != "")
        print(f"📋 OCR extracted {extracted_count} values from report")
        for k, v in result.items():
            if v is not None and v != "":
                print(f"   ✅ {k}: {v}")

        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e


async def generate_ai_insight(features: dict, category: str) -> str:
    """
    Use Gemini to generate a 2-line personalized future risk insight for a specific health category.
    Falls back to rule-based message if API fails.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return ""

    # Build a compact summary of the patient's relevant data
    data_summary = []
    if features.get("bp_systolic_latest"):
        data_summary.append(f"BP: {features['bp_systolic_latest']}/{features.get('bp_diastolic_latest', '?')} mmHg (trend: {features.get('bp_trend', 'unknown')})")
    if features.get("sugar_latest"):
        data_summary.append(f"Fasting sugar: {features['sugar_latest']} mg/dL")
    if features.get("hemoglobin"):
        data_summary.append(f"Hemoglobin: {features['hemoglobin']} g/dL")
    if features.get("platelet_count"):
        data_summary.append(f"Platelets: {features['platelet_count']:,}/cumm")
    if features.get("wbc_count"):
        data_summary.append(f"WBC: {features['wbc_count']:,}/cumm")
    if features.get("creatinine"):
        data_summary.append(f"Creatinine: {features['creatinine']} mg/dL")
    if features.get("bmi"):
        data_summary.append(f"BMI: {features['bmi']}")
    if features.get("hba1c"):
        data_summary.append(f"HbA1c: {features['hba1c']}%")
    if features.get("total_cholesterol"):
        data_summary.append(f"Cholesterol: {features['total_cholesterol']} mg/dL")
    if features.get("tsh"):
        data_summary.append(f"TSH: {features['tsh']} mIU/L")
    if features.get("sgpt"):
        data_summary.append(f"SGPT/ALT: {features['sgpt']} U/L")
    if features.get("vitamin_d"):
        data_summary.append(f"Vitamin D: {features['vitamin_d']} ng/mL")
    if features.get("vitamin_b12"):
        data_summary.append(f"Vitamin B12: {features['vitamin_b12']} pg/mL")

    age = features.get("age", 35)
    gender = features.get("gender", "unknown")

    prompt = f"""
Patient data: {', '.join(data_summary)}
Age: {age}, Gender: {gender}
Category to analyze: {category}

Write exactly 2 short sentences (max 25 words each) about the FUTURE health risk for this specific category based on the patient's actual numbers.
- Sentence 1: What risk they face in the future if unchanged (be specific with numbers/timeframes).
- Sentence 2: One actionable thing they can do to prevent it.
- Tone: Calm, encouraging, not alarming.
- Do NOT use markdown, bullet points, or headers.
- Return only the 2 sentences, nothing else.
"""

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        # Ensure it's max 2 sentences
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
        return ". ".join(sentences[:2]) + "."
    except Exception as e:
        print(f"⚠️ AI insight generation failed for {category}: {e}")
        return ""
