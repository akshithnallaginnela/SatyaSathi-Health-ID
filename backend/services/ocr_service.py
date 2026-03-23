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
    if cleaned.startswith("" * 3 + "json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("" * 3):
        cleaned = cleaned[3:]
    if cleaned.endswith("" * 3):
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
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        base_prompt = """
You are extracting values from an Indian medical lab report.
The report may be from Drlogy, Redcliffe, Healthians, Apollo,
Bio Rad, or any Indian government or private hospital lab.

Extract ONLY these values (use null if not present):
{
  "hemoglobin": number,
  "rbc_count": number,
  "pcv": number,
  "mcv": number,
  "mch": number,
  "mchc": number,
  "rdw": number,
  "wbc_count": number,
  "neutrophils_pct": number,
  "lymphocytes_pct": number,
  "monocytes_pct": number,
  "eosinophils_pct": number,
  "basophils_pct": number,
  "platelet_count": number,
  "fasting_glucose": number,
  "random_glucose": number,
  "urea": number,
  "creatinine": number,
  "lab_name": string,
  "report_date": string,
  "lab_interpretation": string
}

Handle all label variants:
  hemoglobin: Hb, HGB, HAEMOGLOBIN, Haemoglobin, Hemoglobin
  wbc_count: TLC, WBC COUNT, Total WBC count, Total Leucocyte Count
  platelet_count: PLT, Platelet Count, PLATELET COUNT, Platelets
  fasting_glucose: FBS, Fasting Blood Sugar, Fasting Glucose,
                   GLUCOSE FASTING, Blood Glucose
  random_glucose: RBS, Random Blood Sugar, GLUCOSE RANDOM
  pcv: HCT, Hematocrit, Packed Cell Volume, PCV

Convert all values to standard units:
  WBC: if given as 10^3/uL multiply by 1000 to get /cumm
  RBC: if given as 10^6/uL keep as-is in millions
  Platelets: if given as 10^3/uL multiply by 1000

Return ONLY valid JSON, no explanation, no markdown.
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
