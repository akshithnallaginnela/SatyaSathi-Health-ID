import os
import json
import google.generativeai as genai
from PIL import Image
import io
from pydantic import BaseModel, ValidationError

# Optional: Load env variable directly if not already done by main.py
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))


class OCRPayload(BaseModel):
    document_type: str | None = None
    patient_name: str | None = None
    date: str | None = None
    doctor: str | None = None
    key_findings: list[str] = []
    medications: list[str] = []


def _clean_json_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def _validate_payload(raw: dict) -> dict:
    # Normalize list-like fields if model returned single strings.
    if isinstance(raw.get("key_findings"), str):
        raw["key_findings"] = [raw["key_findings"]]
    if isinstance(raw.get("medications"), str):
        raw["medications"] = [raw["medications"]]

    payload = OCRPayload.model_validate(raw)
    return payload.model_dump()

async def process_health_document(image_bytes: bytes) -> dict:
    """
    Takes an image (prescription, blood test, etc.) and uses Gemini 1.5 Flash
    to extract vital health information into a structured JSON dictionary.
    """
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY is not set in the environment.")
    
    try:
        # Load image with PIL
        image = Image.open(io.BytesIO(image_bytes))
        
        # We use the fast and affordable gemini-1.5-flash for OCR
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        base_prompt = """
        You are an expert medical data extractor. I am providing an image of a health document.
        Return ONLY a valid JSON object with exactly these keys:
        {
          "document_type": string|null,
          "patient_name": string|null,
          "date": string|null,
          "doctor": string|null,
          "key_findings": string[],
          "medications": string[]
        }
        Rules:
        - Do not include markdown.
        - Do not include extra keys.
        - If a value is not visible, use null for strings and [] for arrays.
        - key_findings should contain clinically relevant findings from report text.
        """

        retry_prompt = """
        STRICT MODE: Output only raw JSON with the exact schema requested earlier.
        No prose. No markdown. No additional keys. Ensure valid JSON syntax.
        """

        last_error = None
        for attempt in range(2):
            prompt = base_prompt if attempt == 0 else f"{base_prompt}\n\n{retry_prompt}"
            response = model.generate_content([image, prompt])
            text_response = _clean_json_text((response.text or "").strip())
            try:
                parsed = json.loads(text_response)
                return _validate_payload(parsed)
            except (json.JSONDecodeError, ValidationError) as parse_err:
                last_error = parse_err

        raise ValueError(f"OCR output parsing failed after retry: {last_error}")
        
    except Exception as e:
        print(f"Error in Gemini OCR: {e}")
        raise e
