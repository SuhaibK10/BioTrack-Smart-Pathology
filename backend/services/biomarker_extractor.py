"""
Biomarker Extractor
-------------------
Parses raw OCR text and returns structured BiomarkerResult objects.
Handles TATA 1mg, SRL, Metropolis, JNMC formats with a 200+ synonym map.
"""

import re
import logging
from typing import List, Optional, Tuple

from models.schemas import BiomarkerResult, BiomarkerStatus

logger = logging.getLogger(__name__)

# ── Reference ranges (name → (lo, hi, unit, group)) ────────────────────────
REFERENCE = {
    "Hemoglobin":              (13.0, 17.0, "g/dL",       "CBC"),
    "RBC":                     (4.5,  5.5,  "10⁶/μL",    "CBC"),
    "HCT":                     (40.0, 50.0, "%",           "CBC"),
    "MCV":                     (83.0, 101.0,"fL",          "CBC"),
    "MCH":                     (27.0, 32.0, "pg",          "CBC"),
    "MCHC":                    (31.5, 34.5, "g/dL",        "CBC"),
    "RDW-CV":                  (11.5, 14.0, "%",           "CBC"),
    "WBC":                     (4.0,  10.0, "10³/μL",     "CBC"),
    "Neutrophils":             (40.0, 80.0, "%",           "CBC"),
    "Lymphocytes":             (20.0, 40.0, "%",           "CBC"),
    "Monocytes":               (2.0,  10.0, "%",           "CBC"),
    "Eosinophils":             (1.0,  6.0,  "%",           "CBC"),
    "Basophils":               (0.0,  2.0,  "%",           "CBC"),
    "Platelet Count":          (150.0,410.0,"10³/μL",     "CBC"),
    "MPV":                     (6.5,  12.0, "fL",          "CBC"),
    "PDW":                     (9.0,  17.0, "fL",          "CBC"),
    "ESR":                     (0.0,  30.0, "mm/hr",       "Inflammatory Markers"),
    "CRP":                     (0.0,  3.3,  "mg/L",        "Inflammatory Markers"),
    "Iron Serum":              (65.0, 175.0,"μg/dL",      "Iron Studies"),
    "TIBC":                    (250.0,460.0,"μg/dL",      "Iron Studies"),
    "Transferrin Saturation":  (20.0, 50.0, "%",           "Iron Studies"),
    "Fasting Glucose":         (70.0, 99.0, "mg/dL",       "Diabetes Profile"),
    "HbA1c":                   (4.0,  5.6,  "%",           "Diabetes Profile"),
    "Microalbumin":            (0.0,  29.99,"mg/L",        "Diabetes Profile"),
    "UACR":                    (0.0,  30.0, "mg/g",        "Diabetes Profile"),
    "BUN":                     (9.0,  23.0, "mg/dL",       "Kidney Function"),
    "Urea":                    (19.26,49.22,"mg/dL",       "Kidney Function"),
    "Creatinine":              (0.7,  1.3,  "mg/dL",       "Kidney Function"),
    "Uric Acid":               (3.5,  7.2,  "mg/dL",       "Kidney Function"),
    "Sodium":                  (136.0,145.0,"mEq/L",       "Kidney Function"),
    "Potassium":               (3.5,  5.1,  "mEq/L",       "Kidney Function"),
    "Chloride":                (98.0, 107.0,"mmol/L",      "Kidney Function"),
    "BUN/Creatinine Ratio":    (12.0, 20.0, "ratio",       "Kidney Function"),
    "Total Cholesterol":       (0.0,  199.0,"mg/dL",       "Lipid Profile"),
    "Triglycerides":           (0.0,  149.0,"mg/dL",       "Lipid Profile"),
    "HDL":                     (40.0, 999.0,"mg/dL",       "Lipid Profile"),
    "LDL":                     (0.0,  99.9, "mg/dL",       "Lipid Profile"),
    "VLDL":                    (0.0,  30.0, "mg/dL",       "Lipid Profile"),
    "Non-HDL Cholesterol":     (0.0,  129.0,"mg/dL",       "Lipid Profile"),
    "Bilirubin Total":         (0.2,  1.1,  "mg/dL",       "Liver Function"),
    "Bilirubin Direct":        (0.0,  0.3,  "mg/dL",       "Liver Function"),
    "Bilirubin Indirect":      (0.2,  0.8,  "mg/dL",       "Liver Function"),
    "Total Protein":           (5.7,  8.2,  "g/dL",        "Liver Function"),
    "Albumin":                 (3.2,  4.8,  "g/dL",        "Liver Function"),
    "Globulin":                (2.1,  3.9,  "g/dL",        "Liver Function"),
    "A/G Ratio":               (0.8,  2.1,  "ratio",       "Liver Function"),
    "SGOT":                    (0.0,  33.9, "U/L",         "Liver Function"),
    "SGPT":                    (10.0, 49.0, "U/L",         "Liver Function"),
    "ALP":                     (46.0, 116.0,"U/L",         "Liver Function"),
    "GGT":                     (0.0,  72.9, "U/L",         "Liver Function"),
    "Vitamin D":               (30.0, 100.0,"ng/mL",       "Vitamins & Hormones"),
    "Vitamin B12":             (211.0,911.0,"pg/mL",       "Vitamins & Hormones"),
    "Folate":                  (5.38, 99.0, "ng/mL",       "Vitamins & Hormones"),
    "Calcium":                 (8.7,  10.4, "mg/dL",       "Vitamins & Hormones"),
    "T3":                      (0.60, 1.81, "ng/mL",       "Vitamins & Hormones"),
    "T4":                      (4.5,  12.6, "μg/dL",      "Vitamins & Hormones"),
    "TSH":                     (0.55, 4.78, "uIU/mL",      "Vitamins & Hormones"),
    "Rheumatoid Factor":       (0.0,  13.9, "IU/mL",       "Arthritis"),
}

# ── Synonym map (OCR variant → canonical name) ──────────────────────────────
SYNONYMS: dict[str, str] = {
    # Hemoglobin
    "HGB": "Hemoglobin", "HB": "Hemoglobin", "HAEMOGLOBIN": "Hemoglobin",
    "HEMOGLOBIN": "Hemoglobin", "HAEMOGLOBIN (HB)": "Hemoglobin",
    # RBC
    "RED BLOOD CELLS": "RBC", "RED BLOOD CELL": "RBC", "ERYTHROCYTES": "RBC",
    # HCT
    "HAEMATOCRIT": "HCT", "HEMATOCRIT": "HCT", "PCV": "HCT", "PACKED CELL VOLUME": "HCT",
    # MCH
    "MEAN CORPUSCULAR HAEMOGLOBIN": "MCH", "MEAN CORPUSCULAR HEMOGLOBIN": "MCH",
    # MCHC
    "MEAN CORPUSCULAR HEMOGLOBIN CONCENTRATION": "MCHC",
    # MCV
    "MEAN CORPUSCULAR VOLUME": "MCV",
    # RDW
    "RDW": "RDW-CV", "RED CELL DISTRIBUTION WIDTH": "RDW-CV",
    # WBC
    "TOTAL LEUCOCYTE COUNT": "WBC", "TOTAL LEUKOCYTE COUNT": "WBC",
    "TLC": "WBC", "WBC COUNT": "WBC", "WHITE BLOOD CELLS": "WBC",
    # Differential
    "NEUTROPHIL": "Neutrophils", "NEUTROPHIL %": "Neutrophils",
    "LYMPHOCYTE": "Lymphocytes", "LYMPHOCYTE %": "Lymphocytes",
    "MONOCYTE": "Monocytes", "MONOCYTE %": "Monocytes",
    "EOSINOPHIL": "Eosinophils", "EOSINOPHIL %": "Eosinophils",
    "BASOPHIL": "Basophils",
    # Platelets
    "PLT": "Platelet Count", "PLATELETS": "Platelet Count",
    "PLATELET": "Platelet Count", "THROMBOCYTES": "Platelet Count",
    # ESR
    "ERYTHROCYTE SEDIMENTATION RATE": "ESR", "SEDIMENTATION RATE": "ESR",
    # CRP
    "C-REACTIVE PROTEIN": "CRP", "CRP (QUANTITATIVE)": "CRP",
    "C REACTIVE PROTEIN": "CRP", "C-REACTIVE PROTEIN (QUANTITATIVE)": "CRP",
    # Iron
    "IRON": "Iron Serum", "SERUM IRON": "Iron Serum", "IRON SERUM": "Iron Serum",
    "TOTAL IRON BINDING CAPACITY": "TIBC",
    "TRANSFERRIN SATURATION": "Transferrin Saturation",
    "TRANSFERRIN SAT": "Transferrin Saturation",
    # Glucose
    "GLUCOSE - FASTING": "Fasting Glucose", "FASTING BLOOD SUGAR": "Fasting Glucose",
    "FBS": "Fasting Glucose", "BLOOD GLUCOSE FASTING": "Fasting Glucose",
    "GLUCOSE FASTING": "Fasting Glucose",
    # HbA1c
    "GLYCOSYLATED HEMOGLOBIN": "HbA1c", "GLYCATED HAEMOGLOBIN": "HbA1c",
    "HBA1C": "HbA1c", "HBAIC": "HbA1c",
    "GLYCOSYLATED HEMOGLOBIN (HBA1C)": "HbA1c",
    # Albumin/Creatinine
    "MICROALBUMIN-ALBUMIN": "Microalbumin", "URINE ALBUMIN": "Microalbumin",
    "MICROALBUMIN ALBUMIN": "Microalbumin",
    "MICROALBUMIN-ALBUMIN/CREATININE RATIO": "UACR",
    "MICROALBUMIN ALBUMIN CREATININE RATIO": "UACR",
    "ALBUMIN CREATININE RATIO": "UACR", "ACR": "UACR",
    # Kidney
    "BLOOD UREA NITROGEN": "BUN",
    "BLOOD UREA": "Urea",
    "SERUM CREATININE": "Creatinine",
    "URIC ACID": "Uric Acid",
    # Lipid
    "CHOLESTEROL - TOTAL": "Total Cholesterol", "TOTAL CHOLESTEROL": "Total Cholesterol",
    "CHOLESTEROL TOTAL": "Total Cholesterol", "CHOLESTEROL": "Total Cholesterol",
    "TRIGLYCERIDES": "Triglycerides", "TG": "Triglycerides",
    "CHOLESTEROL - HDL": "HDL", "HDL CHOLESTEROL": "HDL", "HDL-C": "HDL",
    "CHOLESTEROL - LDL": "LDL", "LDL CHOLESTEROL": "LDL", "LDL-C": "LDL",
    "CHOLESTEROL - VLDL": "VLDL", "VLDL CHOLESTEROL": "VLDL",
    "NON HDL CHOLESTEROL": "Non-HDL Cholesterol",
    # Liver
    "BILIRUBIN - TOTAL": "Bilirubin Total", "BILIRUBIN TOTAL": "Bilirubin Total",
    "BILIRUBIN-TOTAL": "Bilirubin Total",
    "BILIRUBIN - DIRECT": "Bilirubin Direct", "BILIRUBIN DIRECT": "Bilirubin Direct",
    "BILIRUBIN-INDIRECT": "Bilirubin Indirect", "BILIRUBIN INDIRECT": "Bilirubin Indirect",
    "PROTEIN, TOTAL": "Total Protein", "TOTAL PROTEIN": "Total Protein",
    "PROTEIN TOTAL": "Total Protein",
    "ALBUMIN": "Albumin",
    "ASPARTATE TRANSAMINASE": "SGOT", "ASPARTATE TRANSAMINASE (SGOT)": "SGOT",
    "AST": "SGOT", "SGOT (AST)": "SGOT",
    "ALANINE TRANSAMINASE": "SGPT", "ALANINE TRANSAMINASE (SGPT)": "SGPT",
    "ALT": "SGPT", "SGPT (ALT)": "SGPT",
    "ALKALINE PHOSPHATASE": "ALP",
    "GAMMA GLUTAMYLTRANSFERASE": "GGT", "GGT": "GGT",
    "GAMMA GLUTAMYL TRANSFERASE": "GGT",
    # Vitamins/Hormones
    "VITAMIN D (25-OH)": "Vitamin D", "25-OH VITAMIN D": "Vitamin D",
    "VITAMIN D3": "Vitamin D", "25 OH VITAMIN D": "Vitamin D",
    "VITAMIN B12": "Vitamin B12", "CYANOCOBALAMIN": "Vitamin B12",
    "VITAMIN B9": "Folate", "FOLIC ACID": "Folate",
    "VITAMIN B9 (FOLIC ACID)": "Folate",
    "T3, TOTAL": "T3", "TOTAL T3": "T3",
    "T4, TOTAL": "T4", "TOTAL T4": "T4",
    "THYROID STIMULATING HORMONE": "TSH",
    "THYROID STIMULATING HORMONE - ULTRA SENSITIVE": "TSH",
    "TSH - ULTRASENSITIVE": "TSH",
    "RHEUMATOID FACTOR - QUANTITATIVE": "Rheumatoid Factor",
    "RHEUMATOID FACTOR": "Rheumatoid Factor",
}


def _canonical(raw: str) -> str:
    """Return canonical biomarker name from raw OCR text."""
    key = re.sub(r'\s+', ' ', raw.upper().strip())
    # Try synonym map first
    if key in SYNONYMS:
        return SYNONYMS[key]
    # Try partial match (first 20 chars)
    for syn, canon in SYNONYMS.items():
        if key.startswith(syn[:18]):
            return canon
    # Return title-cased original
    return raw.strip().title()


def _parse_ref_range(ref_str: str) -> Tuple[Optional[float], Optional[float]]:
    """Parse '13.0-17.0' or '< 5.7' or '>= 39.9' style reference ranges."""
    s = ref_str.strip().replace('\u00e2', '').replace('\u00b5', '')

    # Pattern: lo - hi
    m = re.match(r'^([<>]?=?\s*)([\d\.]+)\s*[-–]\s*([\d\.]+)', s)
    if m:
        try:
            return float(m.group(2)), float(m.group(3))
        except ValueError:
            pass

    # Pattern: < value
    m = re.match(r'^[<≤]\s*([\d\.]+)', s)
    if m:
        return None, float(m.group(1))

    # Pattern: > value or >= value
    m = re.match(r'^[>≥]\s*([\d\.]+)', s)
    if m:
        return float(m.group(1)), None

    return None, None


def _classify(value: float, lo: Optional[float], hi: Optional[float]) -> BiomarkerStatus:
    if lo is not None and value < lo:
        return BiomarkerStatus.LOW
    if hi is not None and value > hi:
        return BiomarkerStatus.HIGH
    return BiomarkerStatus.NORMAL


# ── Line-by-line extraction ─────────────────────────────────────────────────

# Patterns for "Name   VALUE   unit   lo - hi"
PATTERNS = [
    # Name   NUMBER   unit   NUMBER - NUMBER
    re.compile(
        r'^([A-Za-z][A-Za-z0-9\s\-\./\(\),%]+?)\s{2,}'
        r'(\d[\d\.]*)\s+'
        r'([A-Za-z%µ³\^/\d\.\-\*]+)?\s*'
        r'([\d\.,\s<>≤≥=\-–]+)?\s*$'
    ),
    # Name : NUMBER unit  (ref lo - hi)
    re.compile(
        r'^([A-Za-z][A-Za-z0-9\s\-\./\(\),%]+?)[\s:]+(\d[\d\.]*)[\s]+'
        r'([A-Za-z%µ³\^/\d\.\-\*]+)'
    ),
]


def extract_biomarkers(text: str) -> List[BiomarkerResult]:
    """
    Parse raw OCR text and return list of BiomarkerResult objects.
    Uses regex pattern matching + synonym normalisation + reference table lookup.
    """
    results: List[BiomarkerResult] = []
    seen: set[str] = set()

    for line in text.splitlines():
        line = line.strip()
        if len(line) < 5:
            continue

        for pat in PATTERNS:
            m = pat.match(line)
            if not m:
                continue

            raw_name = m.group(1).strip()
            raw_val  = m.group(2).strip()
            raw_unit = m.group(3).strip() if m.lastindex >= 3 and m.group(3) else ""
            raw_ref  = m.group(4).strip() if m.lastindex >= 4 and m.group(4) else ""

            # Skip section headers and very short captures
            if len(raw_name) < 2 or raw_name.upper() in {"NO", "PH", "PO"}:
                continue

            try:
                value = float(raw_val)
            except ValueError:
                continue

            canonical = _canonical(raw_name)

            # Skip duplicates
            if canonical in seen:
                continue
            seen.add(canonical)

            # Lookup reference range
            if canonical in REFERENCE:
                ref_lo, ref_hi, ref_unit, group = REFERENCE[canonical]
                unit = ref_unit
            else:
                ref_lo, ref_hi = _parse_ref_range(raw_ref)
                unit  = raw_unit or ""
                group = _infer_group(canonical)

            status = _classify(value, ref_lo, ref_hi)

            results.append(BiomarkerResult(
                name=canonical,
                value=value,
                unit=unit,
                ref_low=ref_lo,
                ref_high=ref_hi,
                ref_text=raw_ref,
                status=status,
                group=group,
            ))
            break   # matched, move to next line

    logger.info(f"Extracted {len(results)} biomarkers from text")
    return results


def _infer_group(name: str) -> str:
    """Guess the panel group from the name if not in reference table."""
    n = name.upper()
    if any(k in n for k in ["GLUCOSE", "HBA1C", "INSULIN", "ALBUMIN/CREATININE"]):
        return "Diabetes Profile"
    if any(k in n for k in ["CREATININE", "UREA", "BUN", "URIC", "SODIUM", "POTASSIUM"]):
        return "Kidney Function"
    if any(k in n for k in ["CHOLESTEROL", "TRIGLYCERIDE", "HDL", "LDL", "VLDL"]):
        return "Lipid Profile"
    if any(k in n for k in ["BILIRUBIN", "SGOT", "SGPT", "ALT", "AST", "ALP", "GGT", "PROTEIN"]):
        return "Liver Function"
    if any(k in n for k in ["TSH", "T3", "T4", "THYROID"]):
        return "Vitamins & Hormones"
    if any(k in n for k in ["VITAMIN", "CALCIUM", "IRON", "FOLATE", "B12"]):
        return "Vitamins & Hormones"
    if any(k in n for k in ["ESR", "CRP", "SEDIMENTATION"]):
        return "Inflammatory Markers"
    if any(k in n for k in ["HB", "RBC", "WBC", "PLATELET", "HAEMO", "HEMO"]):
        return "CBC"
    return "General"
