"""Realistic model inference using trained XGBoost artifacts.

Loads models from backend/ml/models/realistic and predicts:
- overall signal and confidence
- recommended tasks
- diet focus
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any
import pickle
import re

MODEL_DIR = Path(__file__).resolve().parent / "models" / "realistic"


@dataclass
class PredictorResult:
    overall_signal: str
    overall_confidence: float
    diet_focus: str
    task_predictions: dict[str, bool]


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value)
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _pick_numeric(lab: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        if key in lab:
            val = _to_float(lab.get(key))
            if val is not None:
                return val
    return None


def _age_from_user(user: Any) -> float:
    dob = getattr(user, "date_of_birth", None)
    if not dob:
        return 35.0
    try:
        today = date.today()
        return float(today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day)))
    except Exception:
        return 35.0


def _gender_enc(user: Any) -> float:
    gender = str(getattr(user, "gender", "")).lower()
    return 1.0 if gender == "male" else 0.0


@lru_cache(maxsize=1)
def _load_bundles() -> dict[str, Any] | None:
    required = {
        "overall": MODEL_DIR / "overall_signal_model.pkl",
        "task": MODEL_DIR / "task_models.pkl",
        "diet": MODEL_DIR / "diet_model.pkl",
    }
    if not all(path.exists() for path in required.values()):
        return None

    with open(required["overall"], "rb") as f:
        overall_bundle = pickle.load(f)
    with open(required["task"], "rb") as f:
        task_bundle = pickle.load(f)
    with open(required["diet"], "rb") as f:
        diet_bundle = pickle.load(f)

    return {
        "overall": overall_bundle,
        "task": task_bundle,
        "diet": diet_bundle,
    }


def _normalize_platelet(raw: float | None) -> float | None:
    """Normalize platelets: values < 2000 are in x10³/µL units, convert to /µL."""
    if raw is None:
        return None
    return raw * 1000 if raw < 2000 else raw


def _build_feature_map(ocr_data: dict[str, Any], user: Any, body_metrics: Any = None, vitals: Any = None) -> dict[str, float]:
    lab = ocr_data.get("lab_results") or {}
    if not isinstance(lab, dict):
        lab = {}

    # BMI from body_metrics table, fallback to normal
    bmi = 23.0
    waist_cm = 85.0
    if body_metrics is not None:
        bmi = float(getattr(body_metrics, "bmi", None) or 23.0)
        waist_cm = float(getattr(body_metrics, "waist_cm", None) or 85.0)

    # Glucose from vitals table if not in lab results
    vitals_glucose = None
    if vitals is not None:
        vitals_glucose = float(getattr(vitals, "fasting_glucose", None) or 0) or None

    fasting_glucose = _pick_numeric(lab, "fasting_sugar", "fasting_glucose", "glucose") or vitals_glucose or 95.0

    raw_platelets = _pick_numeric(lab, "platelets", "platelet_count", "plt")
    platelet_count = _normalize_platelet(raw_platelets) or 220000.0

    return {
        "hemoglobin": _pick_numeric(lab, "hemoglobin", "hb") or 13.0,
        "rbc_count": _pick_numeric(lab, "rbc_count", "total_rbc_count") or 4.8,
        "pcv": _pick_numeric(lab, "pcv", "packed_cell_volume", "hct") or 40.0,
        "mcv": _pick_numeric(lab, "mcv", "mean_corpuscular_volume") or 85.0,
        "mch": _pick_numeric(lab, "mch") or 28.0,
        "mchc": _pick_numeric(lab, "mchc") or 33.0,
        "rdw": _pick_numeric(lab, "rdw") or 13.0,
        "wbc_count": _pick_numeric(lab, "wbc_count", "total_wbc_count", "tlc") or 7000.0,
        "neutrophils_pct": _pick_numeric(lab, "neutrophils", "neutrophils_pct") or 60.0,
        "lymphocytes_pct": _pick_numeric(lab, "lymphocytes", "lymphocytes_pct") or 30.0,
        "platelet_count": platelet_count,
        "fasting_glucose": fasting_glucose,
        "random_glucose": _pick_numeric(lab, "random_glucose") or 125.0,
        "urea": _pick_numeric(lab, "urea") or 25.0,
        "creatinine": _pick_numeric(lab, "creatinine") or 0.9,
        "age": _age_from_user(user),
        "gender_enc": _gender_enc(user),
        "bmi": bmi,
        "waist_cm": waist_cm,
        "activity_level": 1.0,
        "family_hx_diabetes": 0.0,
        "stress_level": 5.0,
        "smoking": 0.0,
        "sleep_hours_avg": 7.0,
        "water_avg_glasses": 6.0,
        "urgency_score": 4.0,
    }


def predict_from_ocr(ocr_data: dict[str, Any], user: Any, body_metrics: Any = None, vitals: Any = None) -> PredictorResult | None:
    bundles = _load_bundles()
    if bundles is None:
        return None

    import pandas as pd

    feat = _build_feature_map(ocr_data, user, body_metrics=body_metrics, vitals=vitals)

    overall = bundles["overall"]
    row_overall = pd.DataFrame([{f: feat.get(f, 0.0) for f in overall["features"]}])
    pred_idx = int(overall["model"].predict(row_overall)[0])
    pred_signal = str(overall["label_encoder"].inverse_transform([pred_idx])[0])
    prob = overall["model"].predict_proba(row_overall)[0]
    conf = float(max(prob))

    task = bundles["task"]
    row_task = pd.DataFrame([{f: feat.get(f, 0.0) for f in task["features"]}])
    task_predictions = {k: bool(m.predict(row_task)[0]) for k, m in task["models"].items()}

    diet = bundles["diet"]
    row_diet = pd.DataFrame([{f: feat.get(f, 0.0) for f in diet["features"]}])
    diet_idx = int(diet["model"].predict(row_diet)[0])
    diet_focus = str(diet["label_encoder"].inverse_transform([diet_idx])[0])

    return PredictorResult(
        overall_signal=pred_signal,
        overall_confidence=conf,
        diet_focus=diet_focus,
        task_predictions=task_predictions,
    )
