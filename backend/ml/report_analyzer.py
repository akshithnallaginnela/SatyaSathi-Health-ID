"""Hybrid health risk analyzer.

This module supports two inference modes:
1) Trained model inference (if a model artifact exists)
2) Rule-based fallback/safety override

The trained model is expected at: backend/ml/models/risk_model.joblib
"""

from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from typing import Any

import joblib

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

MODEL_ARTIFACT_PATH = Path(__file__).resolve().parent / "models" / "risk_model.joblib"


@lru_cache(maxsize=1)
def _load_trained_model() -> dict[str, Any] | None:
    """Load trained model artifact once per process."""
    model_path_override = os.getenv("RISK_MODEL_PATH")
    artifact_path = Path(model_path_override) if model_path_override else MODEL_ARTIFACT_PATH
    if not artifact_path.exists():
        return None

    try:
        artifact = joblib.load(artifact_path)
        if isinstance(artifact, dict) and "pipeline" in artifact:
            return artifact
    except Exception:
        return None
    return None


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


def _rule_based_assessment(ocr_data: dict[str, Any]) -> dict[str, Any]:
    full_text = _flatten_findings(ocr_data)

    high_hits = _scan_text(full_text, HIGH_RISK_KEYWORDS)
    moderate_hits = _scan_text(full_text, MODERATE_RISK_KEYWORDS)
    high_med_hits = _scan_text(full_text, HIGH_RISK_MEDICATIONS)
    moderate_med_hits = _scan_text(full_text, MODERATE_RISK_MEDICATIONS)

    import re
    lab_results = ocr_data.get("lab_results") or {}
    if isinstance(lab_results, dict):
        # Numeric Hemoglobin Check
        hb_str = str(lab_results.get("hemoglobin") or "")
        match = re.search(r"(\d+(\.\d+)?)", hb_str)
        if match:
            try:
                hb_val = float(match.group(1))
                if hb_val < 7.0:
                    high_hits.append("severe anemia")
                elif hb_val < 13.0:
                    moderate_hits.append("low hemoglobin")
            except ValueError:
                pass
                
        # Numeric Glucose Check
        fs_str = str(lab_results.get("fasting_sugar") or lab_results.get("glucose") or "")
        match = re.search(r"(\d+(\.\d+)?)", fs_str)
        if match:
            try:
                fs_val = float(match.group(1))
                if fs_val > 250:
                    high_hits.append("fasting glucose > 250")
                elif fs_val > 100:
                    moderate_hits.append("glucose elevated")
            except ValueError:
                pass

    flags: list[str] = []
    for hit in high_hits:
        flags.append(f"High-risk finding: {hit.title()}")
    for hit in high_med_hits:
        flags.append(f"High-risk medication: {hit.title()}")
    for hit in moderate_hits:
        if hit not in high_hits:
            flags.append(f"Moderate finding: {hit.title()}")
    for hit in moderate_med_hits:
        if hit not in high_med_hits:
            flags.append(f"Medication noted: {hit.title()}")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_flags = []
    for f in flags:
        if f not in seen:
            seen.add(f)
            unique_flags.append(f)

    score = len(high_hits) * 3 + len(high_med_hits) * 2 + len(moderate_hits) + len(moderate_med_hits) * 0.5

    if high_hits or high_med_hits or score >= 5:
        return {
            "risk_level": "high",
            "flags": unique_flags,
            "confidence": min(0.95, 0.70 + len(high_hits) * 0.05),
            "summary": (
                "This report contains critical markers that suggest urgent medical attention. "
                "Please consult your doctor immediately."
            ),
            "critical_hits": len(high_hits) + len(high_med_hits),
        }

    if moderate_hits or moderate_med_hits or score >= 1:
        return {
            "risk_level": "moderate",
            "flags": unique_flags,
            "confidence": min(0.90, 0.60 + len(moderate_hits) * 0.05),
            "summary": (
                "Some findings indicate health risks that should be monitored. "
                "Consider scheduling a follow-up with your physician."
            ),
            "critical_hits": 0,
        }

    return {
        "risk_level": "low",
        "flags": unique_flags,
        "confidence": 0.70,
        "summary": "No significant risk markers found in this report. Keep maintaining healthy habits!",
        "critical_hits": 0,
    }


def _model_assessment(ocr_data: dict[str, Any]) -> dict[str, Any] | None:
    artifact = _load_trained_model()
    if artifact is None:
        return None

    try:
        pipeline = artifact["pipeline"]
        text = _flatten_findings(ocr_data)
        predicted_label = str(pipeline.predict([text])[0]).strip().lower()

        confidence = 0.75
        if hasattr(pipeline, "predict_proba"):
            probas = pipeline.predict_proba([text])[0]
            confidence = float(max(probas))

        if predicted_label not in {"low", "moderate", "high"}:
            return None

        return {
            "risk_level": predicted_label,
            "confidence": max(0.0, min(1.0, confidence)),
            "model_version": artifact.get("trained_at", "unknown"),
            "metrics": artifact.get("metrics", {}),
        }
    except Exception:
        return None


def analyze(ocr_data: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze OCR-extracted health data and return a risk assessment.

    Args:
        ocr_data: Dict from Gemini OCR (key_findings, medications, etc.)

    Returns:
        Dict with risk_level, flags, summary, confidence
    """
    rule_result = _rule_based_assessment(ocr_data)
    model_result = _model_assessment(ocr_data)

    if model_result is None:
        final_risk = rule_result["risk_level"]
        final_confidence = float(rule_result["confidence"])
        source = "rules"
    else:
        # Safety-first guardrail: if critical keyword hits exist, don't downgrade high risk.
        if rule_result["critical_hits"] > 0:
            final_risk = "high"
            final_confidence = max(float(rule_result["confidence"]), float(model_result["confidence"]))
            source = "hybrid_guardrail"
        else:
            final_risk = model_result["risk_level"]
            final_confidence = float(model_result["confidence"])
            source = "model"

    if final_risk == "high":
        summary = (
            "This report contains critical markers that suggest urgent medical attention. "
            "Please consult your doctor immediately."
        )
    elif final_risk == "moderate":
        summary = (
            "Some findings indicate health risks that should be monitored. "
            "Consider scheduling a follow-up with your physician."
        )
    else:
        summary = "No significant risk markers found in this report. Keep maintaining healthy habits!"

    doc_type = ocr_data.get("document_type", "Health Document")

    return {
        "risk_level": final_risk,
        "flags": rule_result["flags"],
        "summary": summary,
        "confidence": round(final_confidence, 2),
        "document_type": doc_type,
        "analyzed_fields": list(ocr_data.keys()),
        "inference_source": source,
        "model_info": model_result,
    }
