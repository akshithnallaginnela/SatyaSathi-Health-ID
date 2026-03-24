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
You are a highly precise medical data extraction AI specializing in Indian lab reports.
Extract ALL available health values from this report into a JSON object.

IMPORTANT RULES:
1. Return ONLY raw JSON — no markdown, no explanation, no backticks.
2. Use null for any value not present in the report.
3. All numeric values must be numbers (not strings).
4. For platelet_count: if value is in Lakhs (e.g. "1.5 L" or "1.5 Lakhs"), multiply by 100000. If in thousands (e.g. "150 K"), multiply by 1000.
5. For wbc_count: if in thousands (e.g. "7.5 K" or "7.5 th/cumm"), multiply by 1000.
6. For rbc_count: value is in millions/cumm (e.g. 4.5 to 6.0 range).
7. HCT and PCV are the same — use pcv field.
8. TLC = Total Leucocyte Count = wbc_count.
9. POLYMORPHS = Neutrophils = neutrophils_pct.
10. For peripheral smear findings, capture as a short text string.

Extract these fields:
{
  "hemoglobin": number,           // Hb, HGB, Haemoglobin — g/dL
  "rbc_count": number,            // RBC, Total RBC Count — million/cumm
  "pcv": number,                  // PCV, HCT, Hematocrit — %
  "mcv": number,                  // MCV — fL
  "mch": number,                  // MCH — pg
  "mchc": number,                 // MCHC — g/dL
  "rdw": number,                  // RDW, RDW-CV — %
  "rdw_sd": number,               // RDW-SD — fL
  "mpv": number,                  // MPV, Mean Platelet Volume — fL
  "wbc_count": number,            // WBC, TLC, Total Leucocyte Count — /cumm
  "neutrophils_pct": number,      // Neutrophils, Polymorphs — %
  "lymphocytes_pct": number,      // Lymphocytes — %
  "monocytes_pct": number,        // Monocytes — %
  "eosinophils_pct": number,      // Eosinophils — %
  "basophils_pct": number,        // Basophils — %
  "neutrophils_abs": number,      // Absolute Neutrophil Count — /cumm
  "lymphocytes_abs": number,      // Absolute Lymphocyte Count — /cumm
  "monocytes_abs": number,        // Absolute Monocyte Count — /cumm
  "eosinophils_abs": number,      // Absolute Eosinophil Count — /cumm
  "platelet_count": number,       // PLT, Platelet Count — /cumm (convert if in Lakhs/K)
  "p_lcr": number,                // P-LCR, Platelet Large Cell Ratio — %
  "fasting_glucose": number,      // FBS, Fasting Blood Sugar, Fasting Glucose — mg/dL
  "random_glucose": number,       // RBS, Random Blood Sugar, Random Glucose — mg/dL
  "hba1c": number,                // HbA1c, Glycated Hemoglobin — %
  "urea": number,                 // Urea, Blood Urea — mg/dL
  "creatinine": number,           // Creatinine, Serum Creatinine — mg/dL
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
  "peripheral_smear": string,     // Any peripheral smear findings as text
  "lab_name": string,             // Name of the laboratory
  "report_date": string,          // Date of report
  "lab_interpretation": string    // Doctor's interpretation/conclusion if present
}
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
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        if media_type == "application/pdf":
            contents = [{"mime_type": media_type, "data": file_bytes}, EXTRACTION_PROMPT]
        else:
            image = Image.open(io.BytesIO(file_bytes))
            contents = [image, EXTRACTION_PROMPT]

        response = model.generate_content(contents)
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
