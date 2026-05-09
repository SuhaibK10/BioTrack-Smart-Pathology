"""
Reports Router
--------------
POST /api/reports/upload  — upload PDF/image, run full pipeline, return analysis
GET  /api/reports/{id}    — fetch stored report
"""

import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

import services
from models.schemas import ReportAnalysis

logger   = logging.getLogger(__name__)
router   = APIRouter()
MAX_SIZE = 50 * 1024 * 1024   # 50 MB


@router.post("/upload", response_model=ReportAnalysis)
async def upload_report(
    file:       UploadFile = File(...),
    patient_name: str      = Form("Unknown Patient"),
    patient_age:  int      = Form(0),
    patient_sex:  str      = Form(""),
):
    """
    Full pipeline:
    1. Read uploaded file
    2. OCR extraction
    3. Biomarker parsing
    4. Risk prediction (XGBoost + SHAP)
    5. Alert generation
    6. System health scoring
    7. AI advisory (Gemini or template)
    8. Return ReportAnalysis
    """
    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(413, "File too large (max 50 MB)")

    filename = file.filename or "report.pdf"
    logger.info(f"Processing: {filename} ({len(contents)//1024} KB)")

    # ── Step 1: OCR ──────────────────────────────────────────────────────────
    try:
        raw_text = services.extract_text_from_file(contents, filename)
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        raise HTTPException(422, f"OCR extraction failed: {e}")

    # ── Step 2: Parse biomarkers ─────────────────────────────────────────────
    biomarkers = services.extract_biomarkers(raw_text)
    if not biomarkers:
        raise HTTPException(422, "No biomarkers could be extracted from this report. "
                                  "Ensure the file is a readable lab report.")

    abnormal = [b for b in biomarkers if b.status.value != "NORMAL"]

    # ── Step 3: Risk prediction ──────────────────────────────────────────────
    risks = services.predict(biomarkers)

    # ── Step 4: Alerts ───────────────────────────────────────────────────────
    alerts = services.generate_alerts(biomarkers)

    # ── Step 5: System health ────────────────────────────────────────────────
    system_health = services.compute_system_health(biomarkers)

    # ── Step 6: Advisory ─────────────────────────────────────────────────────
    patient_ctx = {"name": patient_name, "age": patient_age, "sex": patient_sex}
    advisory    = services.generate(biomarkers, risks, alerts, patient_ctx)

    # ── Step 7: Assemble response ─────────────────────────────────────────────
    critical_flags = sum(1 for a in alerts if a.severity.value == "critical")

    return ReportAnalysis(
        patient={"name": patient_name, "age": patient_age, "sex": patient_sex},
        biomarkers=biomarkers,
        abnormal=abnormal,
        alerts=alerts,
        risk_scores=risks,
        system_health=system_health,
        advisory=advisory,
        stats={
            "total":          len(biomarkers),
            "abnormal":       len(abnormal),
            "critical_flags": critical_flags,
            "systems_reviewed": len(system_health),
        },
    )
