import os
import json
import google.generativeai as genai
from PIL import Image
import io

# Optional: Load env variable directly if not already done by main.py
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

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
        
        prompt = """
        You are an expert medical data extractor. I am providing an image of a health document (which could be a prescription, a lab report, blood test results, etc.).
        
        Please extract the key medical information from this document and return ONLY a valid JSON object. 
        Do not include markdown tags like ```json or anything else. Only output the raw JSON string.

        Try to extract the following fields if present:
        - "document_type": e.g., "Prescription", "Blood Test", "Clinical Summary", etc.
        - "patient_name": The name of the patient.
        - "date": The date of the document.
        - "doctor": The name of the doctor or clinic.
        - "key_findings": A list of strings detailing key diagnoses, test results, or instructions.
        - "medications": A list of strings if any medicines are prescribed.
        
        If a field isn't found, leave it empty or null.
        """
        
        # Generate content
        response = model.generate_content([image, prompt])
        text_response = response.text.strip()
        
        # Clean up possible markdown wrappers if the model didn't listen
        if text_response.startswith('```json'):
            text_response = text_response[7:-3].strip()
        elif text_response.startswith('```'):
            text_response = text_response[3:-3].strip()
            
        return json.loads(text_response)
        
    except Exception as e:
        print(f"Error in Gemini OCR: {e}")
        raise e
