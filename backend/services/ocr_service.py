import os
import json
import base64
import io
from PIL import Image
from pydantic import BaseModel, Field

class OCRPayload(BaseModel):
    hemoglobin: float | None = None
    rbc_count: float | None = None
    pcv: float | None = None
    mcv: float | None = None
    mch: float | None = None
    mchc: float | None = None
    rdw: float | None = None
    wbc_count: int | None = None
    neutrophils_pct: float | None = None
    lymphocytes_pct: float | None = None
    monocytes_pct: float | None = None
    eosinophils_pct: float | None = None
    basophils_pct: float | None = None
    platelet_count: int | None = None
    fasting_glucose: float | None = None
    random_glucose: float | None = None
    urea: float | None = None
    creatinine: float | None = None
    lab_name: str | None = None
    report_date: str | None = None
    lab_interpretation: str | None = None

def _clean_json_text(text: str) -> str:
    cleaned = text.strip()
    # Remove markdown code block markers
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    
    return cleaned.strip()

async def extract_report_values(file_path: str) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in the environment.")
    
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    ext = file_path.lower().split(".")[-1]
    if ext in ["jpg","jpeg"]:
        media_type = "image/jpeg"
    elif ext == "png":
        media_type = "image/png"
    elif ext == "pdf":
        media_type = "application/pdf"
    else:
        media_type = "image/jpeg"
        
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        
        base_prompt = """
You are a highly precise medical data extraction AI. Your task is to extract structured health markers from Indian medical lab reports.
The report could be from major labs like Drlogy, Metropolis, SRL, Dr Lal PathLabs, Apollo, or a local diagnostic center.

Extract ONLY these specific values into a JSON object. If a value is missing or unreadable, use null.
Fields:
- "hemoglobin": number (e.g. 13.5)
- "rbc_count": number (e.g. 4.5)
- "pcv": number (e.g. 40.0)
- "mcv": number (e.g. 85.0)
- "mch": number (e.g. 28.0)
- "mchc": number (e.g. 33.0)
- "rdw": number (e.g. 12.5)
- "wbc_count": number (e.g. 7500)
- "neutrophils_pct": number (e.g. 60.0)
- "lymphocytes_pct": number (e.g. 30.0)
- "monocytes_pct": number (e.g. 5.0)
- "eosinophils_pct": number (e.g. 3.0)
- "basophils_pct": number (e.g. 1.0)
- "platelet_count": number (e.g. 250000)
- "fasting_glucose": number (e.g. 95.0)
- "random_glucose": number (e.g. 110.0)
- "urea": number (e.g. 25.0)
- "creatinine": number (e.g. 0.9)
- "lab_name": string
- "report_date": string (ISO format preferred)
- "lab_interpretation": string (Short summary of findings)

STRATEGIES FOR ACCURACY:
1. HEMOGLOBIN: Look for 'Hb', 'HGB', 'Haemoglobin'. Units: g/dL.
2. PLATELETS: Look for 'PLT', 'Platelet Count'. If the value is like '1.5' or '2.0', check if units are 'Lakhs'. Convert to cells/cumm (e.g., 1.5 Lakhs -> 150000).
3. GLUCOSE: 'FBS' or 'Fasting Blood Sugar' -> fasting_glucose. 'RBS' or 'Random Blood Sugar' -> random_glucose.
4. WHITE BLOOD CELLS: 'WBC', 'Total Leucocyte Count' or 'TLC'.
5. CREATININE/UREA: Usually under 'Kidney Function Test' or 'KFT'.

RESPONSE FORMAT: Return ONLY the raw JSON object. No explanation, no backticks, no markdown.
"""
        
        if media_type == "application/pdf":
            contents = [
                {"mime_type": media_type, "data": file_bytes},
                base_prompt
            ]
        else:
            image = Image.open(io.BytesIO(file_bytes))
            contents = [image, base_prompt]
            
        response = model.generate_content(contents)
        raw_text = (response.text or "").strip()
        
        text_response = _clean_json_text(raw_text)
        parsed = json.loads(text_response)
        
        payload = OCRPayload.model_validate(parsed)
        return payload.model_dump()

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e
