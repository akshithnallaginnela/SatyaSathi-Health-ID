"""
ML Report Analyzer — rule-based risk classifier for health documents.

Takes the structured JSON output from OCR (Gemini Vision) and produces
a risk assessment without needing any trained model. Fast, offline,
interpretable — ideal for the prototype.

Output schema:
{
  "risk_level": "low" | "moderate" | "high",
  "flags": [...],
  "summary": str,
  "confidence": float (0–1)
}
"""

from __future__ import annotations
import re
from typing import Any

# ── Risk keyword banks ─────────────────────────────────────────────────────

HIGH_RISK_KEYWORDS = [
    # Glucose / Diabetes
    "hyperglycemia", "diabetic ketoacidosis", "dka", "hba1c > 9", "hba1c>9",
    "fasting glucose > 250", "glucose: 250", "glucose: 300", "glucose: 350",
    "blood sugar 250", "blood sugar 300",
    # Cardiac
    "myocardial infarction", "heart attack", "cardiac arrest", "st elevation",
    "stemi", "nstemi", "acute coronary", "unstable angina", "ventricular fibrillation",
    "ejection fraction < 40", "ejection fraction <40",
    # Hypertension
    "hypertensive crisis", "bp > 180", "bp 180", "systolic > 180",
    "blood pressure 180", "blood pressure 190", "blood pressure 200",
    # Kidney
    "renal failure", "acute kidney injury", "aki", "creatinine > 5",
    # Liver
    "hepatic failure", "liver failure", "cirrhosis",
    # Respiratory
    "respiratory failure", "pulmonary embolism", "spo2 < 90",
    # Anemia
    "hemoglobin < 7", "hb < 7", "severe anemia",
    # Stroke
    "stroke", "transient ischemic attack", "tia", "cerebrovascular",
]

MODERATE_RISK_KEYWORDS = [
    # Glucose
    "prediabetes", "impaired fasting", "hba1c > 6.5", "hba1c 7", "hba1c 8",
    "glucose elevated", "high glucose", "blood sugar elevated",
    # BP
    "hypertension", "elevated blood pressure", "high bp", "bp > 140",
    "systolic > 140", "stage 2 hypertension", "stage 1 hypertension",
    # Lipids
    "high cholesterol", "hyperlipidemia", "ldl > 160", "triglycerides > 200",
    "dyslipidemia",
    # Cardiac
    "arrhythmia", "atrial fibrillation", "afib", "tachycardia", "bradycardia",
    "cardiomegaly", "left ventricular hypertrophy",
    # Kidney
    "proteinuria", "microalbuminuria", "creatinine elevated",
    # Metabolic
    "obesity", "overweight", "bmi > 30",
    # Inflammation
    "elevated crp", "elevated esr", "inflammation",
    # Anemia
    "anemia", "low hemoglobin", "iron deficiency",
    # Thyroid
    "hypothyroidism", "hyperthyroidism", "thyroid dysfunction",
]

HIGH_RISK_MEDICATIONS = [
    "insulin", "warfarin", "heparin", "metformin 2000", "digoxin",
    "nitroglycerin", "amiodarone", "lithium", "clozapine",
]

MODERATE_RISK_MEDICATIONS = [
    "metformin", "glipizide", "glyburide", "glimepiride",
    "amlodipine", "losartan", "lisinopril", "atenolol",
    "rosuvastatin", "atorvastatin", "simvastatin",
    "levothyroxine", "aspirin",
]


def _normalize(text: str) -> str:
    return text.lower().strip()


def _scan_text(text: str, keywords: list[str]) -> list[str]:
    """Returns the keywords found in the text."""
    norm = _normalize(text)
    return [kw for kw in keywords if kw in norm]


def _flatten_findings(data: dict[str, Any]) -> str:
    """Flatten all relevant fields from the OCR JSON into a single string for scanning."""
    parts: list[str] = []
    for key in ("key_findings", "medications", "document_type", "summary", "notes"):
        value = data.get(key)
        if isinstance(value, list):
            parts.extend([str(v) for v in value])
        elif isinstance(value, str) and value:
            parts.append(value)
    return " ".join(parts)


def analyze(ocr_data: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze OCR-extracted health data and return a risk assessment.

    Args:
        ocr_data: Dict from Gemini OCR (key_findings, medications, etc.)

    Returns:
        Dict with risk_level, flags, summary, confidence
    """
    full_text = _flatten_findings(ocr_data)

    high_hits = _scan_text(full_text, HIGH_RISK_KEYWORDS)
    moderate_hits = _scan_text(full_text, MODERATE_RISK_KEYWORDS)
    high_med_hits = _scan_text(full_text, HIGH_RISK_MEDICATIONS)
    moderate_med_hits = _scan_text(full_text, MODERATE_RISK_MEDICATIONS)

    flags: list[str] = []
    for hit in high_hits:
        flags.append(f"⚠️ High-risk finding: {hit.title()}")
    for hit in high_med_hits:
        flags.append(f"💊 High-risk medication: {hit.title()}")
    for hit in moderate_hits:
        if hit not in high_hits:
            flags.append(f"🟡 Moderate finding: {hit.title()}")
    for hit in moderate_med_hits:
        if hit not in high_med_hits:
            flags.append(f"💊 Medication noted: {hit.title()}")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_flags = []
    for f in flags:
        if f not in seen:
            seen.add(f)
            unique_flags.append(f)

    # Score & classify
    score = len(high_hits) * 3 + len(high_med_hits) * 2 + len(moderate_hits) + len(moderate_med_hits) * 0.5

    if high_hits or high_med_hits or score >= 5:
        risk_level = "high"
        summary = (
            "This report contains critical markers that suggest urgent medical attention. "
            "Please consult your doctor immediately."
        )
        confidence = min(0.95, 0.70 + len(high_hits) * 0.05)
    elif moderate_hits or moderate_med_hits or score >= 1:
        risk_level = "moderate"
        summary = (
            "Some findings indicate health risks that should be monitored. "
            "Consider scheduling a follow-up with your physician."
        )
        confidence = min(0.90, 0.60 + len(moderate_hits) * 0.05)
    else:
        risk_level = "low"
        summary = "No significant risk markers found in this report. Keep maintaining healthy habits!"
        confidence = 0.70  # We can't be certain without clinical context

    doc_type = ocr_data.get("document_type", "Health Document")

    return {
        "risk_level": risk_level,
        "flags": unique_flags,
        "summary": summary,
        "confidence": round(confidence, 2),
        "document_type": doc_type,
        "analyzed_fields": list(ocr_data.keys()),
    }
