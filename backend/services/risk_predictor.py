"""
Risk Predictor
--------------
XGBoost-based risk prediction for 5 chronic disease categories.
Falls back to rule-based scoring when model files are absent.
SHAP explainability included.
"""

import os
import logging
import numpy as np
from typing import List, Dict, Any

from models.schemas import BiomarkerResult, RiskResult, ShapEntry, BiomarkerStatus

logger = logging.getLogger(__name__)

# ── Feature extraction ───────────────────────────────────────────────────────

def _get_value(biomarkers: List[BiomarkerResult], name: str, default: float = 0.0) -> float:
    for b in biomarkers:
        if b.name == name:
            return b.value
    return default

def _is_high(biomarkers: List[BiomarkerResult], name: str) -> float:
    for b in biomarkers:
        if b.name == name:
            return 1.0 if b.status == BiomarkerStatus.HIGH else 0.0
    return 0.0

def _is_low(biomarkers: List[BiomarkerResult], name: str) -> float:
    for b in biomarkers:
        if b.name == name:
            return 1.0 if b.status == BiomarkerStatus.LOW else 0.0
    return 0.0


# ── Rule-based risk scores (used when no ML model is trained) ────────────────

def _rule_anaemia(bm: List[BiomarkerResult]) -> float:
    score = 0.0
    if _is_low(bm, "Hemoglobin"):     score += 0.30
    if _is_low(bm, "Iron Serum"):     score += 0.25
    if _is_low(bm, "Transferrin Saturation"): score += 0.20
    if _is_high(bm, "RDW-CV"):        score += 0.15
    if _is_high(bm, "MPV"):           score += 0.05
    if _is_high(bm, "ESR"):           score += 0.05
    return min(score, 1.0)

def _rule_inflammation(bm: List[BiomarkerResult]) -> float:
    score = 0.0
    esr = _get_value(bm, "ESR", 0)
    crp = _get_value(bm, "CRP", 0)
    if esr > 30:  score += min((esr - 30) / 70, 0.45)
    if crp > 3.3: score += min((crp - 3.3) / 10, 0.45)
    if _is_high(bm, "WBC"): score += 0.10
    return min(score, 1.0)

def _rule_thyroid(bm: List[BiomarkerResult]) -> float:
    tsh = _get_value(bm, "TSH", 0)
    if tsh == 0:
        return 0.0
    if tsh > 10:  return 0.95
    if tsh > 4.78:
        return 0.4 + min((tsh - 4.78) / 10, 0.55)
    if tsh < 0.55:
        return 0.6
    return 0.05

def _rule_renal(bm: List[BiomarkerResult]) -> float:
    score = 0.0
    uacr = _get_value(bm, "UACR", 0)
    creat = _get_value(bm, "Creatinine", 0)
    bun   = _get_value(bm, "BUN", 0)
    if uacr > 30:   score += min((uacr - 30) / 270, 0.40)
    if creat > 1.3: score += min((creat - 1.3) / 2, 0.30)
    if bun > 23:    score += min((bun - 23) / 40, 0.20)
    if _is_high(bm, "Urea"): score += 0.10
    return min(score, 1.0)

def _rule_vitamin_def(bm: List[BiomarkerResult]) -> float:
    score = 0.0
    vitd = _get_value(bm, "Vitamin D", 30)
    fol  = _get_value(bm, "Folate", 5.38)
    b12  = _get_value(bm, "Vitamin B12", 400)
    if vitd < 20:  score += 0.40
    elif vitd < 30: score += 0.20
    if fol < 3.37: score += 0.35
    elif fol < 5.38: score += 0.15
    if b12 < 211:  score += 0.25
    return min(score, 1.0)


# ── SHAP approximation (gradient-free sensitivity analysis) ─────────────────

def _shap_for_category(bm: List[BiomarkerResult], category: str) -> List[ShapEntry]:
    """
    Compute approximate SHAP values by measuring score change when each
    abnormal biomarker is reset to its reference midpoint.
    """
    base   = _score_category(bm, category)
    shaps  = []

    for b in bm:
        if b.status == BiomarkerStatus.NORMAL:
            continue

        # Temporarily replace with normal value
        mid  = ((b.ref_low or 0) + (b.ref_high or 0)) / 2 if b.ref_low and b.ref_high else b.value
        orig = b.value
        b.value  = mid
        b.status = BiomarkerStatus.NORMAL
        new_score = _score_category(bm, category)
        b.value  = orig
        b.status = _classify_status(b)

        impact = base - new_score
        if abs(impact) > 0.005:
            shaps.append(ShapEntry(
                feature=b.name,
                impact=round(abs(impact), 3),
                positive=impact > 0,
            ))

    shaps.sort(key=lambda x: x.impact, reverse=True)
    return shaps[:5]


def _classify_status(b: BiomarkerResult) -> BiomarkerStatus:
    if b.ref_low is not None and b.value < b.ref_low:
        return BiomarkerStatus.LOW
    if b.ref_high is not None and b.value > b.ref_high:
        return BiomarkerStatus.HIGH
    return BiomarkerStatus.NORMAL


def _score_category(bm: List[BiomarkerResult], category: str) -> float:
    fns = {
        "Iron-Deficiency Anaemia":    _rule_anaemia,
        "Systemic Inflammation":      _rule_inflammation,
        "Thyroid Dysfunction":        _rule_thyroid,
        "Renal Involvement":          _rule_renal,
        "Vitamin & Folate Deficiency":_rule_vitamin_def,
    }
    fn = fns.get(category)
    return fn(bm) if fn else 0.0


def _label(score: float) -> str:
    if score >= 0.80: return "High Risk"
    if score >= 0.55: return "Moderate Risk"
    if score >= 0.30: return "Borderline"
    return "Low Risk"


# ── Try loading XGBoost model (if trained and saved) ────────────────────────

_MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "models")

def _try_xgb(bm: List[BiomarkerResult], category: str) -> float | None:
    """Attempt XGBoost inference if model file exists."""
    try:
        import xgboost as xgb
        slug = category.lower().replace(" ", "_").replace("-", "_")
        path = os.path.join(_MODEL_DIR, f"{slug}.ubj")
        if not os.path.exists(path):
            return None
        model = xgb.Booster()
        model.load_model(path)
        feat  = _build_feature_vector(bm)
        dm    = xgb.DMatrix([feat])
        return float(model.predict(dm)[0])
    except Exception as e:
        logger.debug(f"XGBoost inference skipped ({category}): {e}")
        return None


def _build_feature_vector(bm: List[BiomarkerResult]) -> List[float]:
    """Build a fixed-length feature vector for XGBoost inference."""
    fields = [
        ("Hemoglobin", "value"), ("Iron Serum", "value"), ("Transferrin Saturation", "value"),
        ("RDW-CV", "value"), ("WBC", "value"), ("ESR", "value"), ("CRP", "value"),
        ("TSH", "value"), ("T3", "value"), ("T4", "value"),
        ("Creatinine", "value"), ("BUN", "value"), ("Urea", "value"), ("UACR", "value"),
        ("Vitamin D", "value"), ("Folate", "value"), ("Vitamin B12", "value"),
        ("HbA1c", "value"), ("Fasting Glucose", "value"),
        ("LDL", "value"), ("HDL", "value"), ("Triglycerides", "value"),
        ("Hemoglobin", "status"), ("Iron Serum", "status"), ("ESR", "status"),
        ("TSH", "status"), ("Vitamin D", "status"),
    ]
    vec = []
    for name, attr in fields:
        if attr == "value":
            vec.append(_get_value(bm, name, 0.0))
        else:
            s = BiomarkerStatus.NORMAL
            for b in bm:
                if b.name == name:
                    s = b.status
                    break
            vec.append(0.0 if s == BiomarkerStatus.NORMAL else (1.0 if s == BiomarkerStatus.HIGH else -1.0))
    return vec


# ── Public API ───────────────────────────────────────────────────────────────

CATEGORIES = [
    "Iron-Deficiency Anaemia",
    "Systemic Inflammation",
    "Thyroid Dysfunction",
    "Renal Involvement",
    "Vitamin & Folate Deficiency",
]

def predict(biomarkers: List[BiomarkerResult]) -> List[RiskResult]:
    """Run risk prediction for all categories."""
    results = []
    for cat in CATEGORIES:
        score = _try_xgb(biomarkers, cat)
        if score is None:
            score = _score_category(biomarkers, cat)
        shap  = _shap_for_category(biomarkers, cat)
        results.append(RiskResult(
            category=cat,
            score=round(score, 3),
            label=_label(score),
            shap=shap,
        ))
    return results
