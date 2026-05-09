"""
Alert Engine
------------
Generates prioritised clinical alerts from abnormal biomarkers.
"""

from typing import List
from models.schemas import BiomarkerResult, AlertItem, AlertSeverity, BiomarkerStatus


# Alert rules: (canonical_name → (severity, title, detail, system))
ALERT_RULES = {
    "TSH": (
        AlertSeverity.CRITICAL,
        "Thyroid Stimulating Hormone Elevated",
        "TSH above reference range — evaluate for hypothyroidism. Repeat TFT with Free T3/T4.",
        "Thyroid",
    ),
    "Hemoglobin": (
        AlertSeverity.CRITICAL,
        "Haemoglobin Below Normal",
        "Haemoglobin low — combined with iron/transferrin status indicates iron-deficiency anaemia.",
        "Haematology",
    ),
    "ESR": (
        AlertSeverity.CRITICAL,
        "Erythrocyte Sedimentation Rate Elevated",
        "ESR significantly elevated — indicates active systemic inflammation. Correlate with CRP.",
        "Inflammatory",
    ),
    "CRP": (
        AlertSeverity.CRITICAL,
        "C-Reactive Protein Elevated",
        "CRP above upper limit — acute-phase response. Combined with elevated ESR demands aetiology workup.",
        "Inflammatory",
    ),
    "Iron Serum": (
        AlertSeverity.HIGH,
        "Serum Iron Deficiency",
        "Iron below reference range — consistent with iron-deficiency anaemia or anaemia of chronic disease.",
        "Haematology",
    ),
    "Transferrin Saturation": (
        AlertSeverity.HIGH,
        "Transferrin Saturation Low",
        "Low transferrin saturation confirms iron-deficient erythropoiesis.",
        "Haematology",
    ),
    "RDW-CV": (
        AlertSeverity.HIGH,
        "Red Cell Distribution Width Elevated",
        "Elevated RDW-CV indicates anisocytosis — consistent with iron-deficiency or mixed anaemia.",
        "Haematology",
    ),
    "UACR": (
        AlertSeverity.HIGH,
        "Microalbuminuria — Stage A2",
        "UACR in A2 range (30–299 mg/g) — early CKD/CVD marker. Confirm with 2 further morning samples (ADA 2024).",
        "Renal",
    ),
    "Microalbumin": (
        AlertSeverity.HIGH,
        "Microalbumin Elevated",
        "Urine microalbumin above normal — indicates glomerular injury. Requires UACR confirmation.",
        "Renal",
    ),
    "BUN": (
        AlertSeverity.HIGH,
        "Blood Urea Nitrogen Elevated",
        "BUN above reference — may indicate pre-renal azotaemia or early renal insufficiency.",
        "Renal",
    ),
    "Urea": (
        AlertSeverity.HIGH,
        "Serum Urea Elevated",
        "Urea above reference. Ensure adequate hydration; monitor renal function trend.",
        "Renal",
    ),
    "Uric Acid": (
        AlertSeverity.HIGH,
        "Hyperuricaemia",
        "Uric acid elevated — risk of gout and urate nephropathy. Dietary purine restriction advised.",
        "Renal",
    ),
    "Chloride": (
        AlertSeverity.HIGH,
        "Hyperchloraemia",
        "Chloride above reference range. May indicate hyperchloraemic acidosis — correlate clinically.",
        "Renal",
    ),
    "Vitamin D": (
        AlertSeverity.HIGH,
        "Severe Vitamin D Deficiency",
        "25-OH Vitamin D below 20 ng/mL — severe deficiency. High fracture risk. Urgent supplementation required.",
        "Vitamins",
    ),
    "Folate": (
        AlertSeverity.HIGH,
        "Folate Deficiency",
        "Folate B9 below normal. Risk of megaloblastic anaemia. Folic acid supplementation indicated.",
        "Vitamins",
    ),
    "LDL": (
        AlertSeverity.MODERATE,
        "LDL Cholesterol Above Desirable",
        "LDL above 100 mg/dL — above desirable range. Lifestyle modification and dietary review advised.",
        "Lipids",
    ),
    "ALP": (
        AlertSeverity.MODERATE,
        "Alkaline Phosphatase Elevated",
        "ALP above reference — may indicate hepatobiliary or bone pathology. Clinical correlation required.",
        "Liver",
    ),
    "MPV": (
        AlertSeverity.MODERATE,
        "Mean Platelet Volume Elevated",
        "Elevated MPV may indicate increased platelet activation or destructive thrombocytopaenia.",
        "Haematology",
    ),
    "PDW": (
        AlertSeverity.MODERATE,
        "Platelet Distribution Width Elevated",
        "Elevated PDW indicates platelet anisocytosis — monitor platelet count trend.",
        "Haematology",
    ),
}


def generate_alerts(biomarkers: List[BiomarkerResult]) -> List[AlertItem]:
    """Generate prioritised alert list from abnormal biomarkers."""
    alerts: List[AlertItem] = []

    for bm in biomarkers:
        if bm.status == BiomarkerStatus.NORMAL:
            continue
        if bm.name not in ALERT_RULES:
            continue

        severity, title, detail, system = ALERT_RULES[bm.name]

        # Escalate severity if very far out of range
        if bm.ref_high and bm.status == BiomarkerStatus.HIGH:
            ratio = bm.value / bm.ref_high
            if ratio > 2.5 and severity == AlertSeverity.MODERATE:
                severity = AlertSeverity.HIGH
            elif ratio > 2.5 and severity == AlertSeverity.HIGH:
                severity = AlertSeverity.CRITICAL

        alerts.append(AlertItem(
            severity=severity,
            title=title,
            detail=f"{bm.name}: {bm.value} {bm.unit} "
                   f"(ref {bm.ref_low}–{bm.ref_high}). {detail}",
            system=system,
            marker=bm.name,
            value=bm.value,
            unit=bm.unit,
        ))

    # Sort: critical → high → moderate
    order = {AlertSeverity.CRITICAL: 0, AlertSeverity.HIGH: 1, AlertSeverity.MODERATE: 2}
    alerts.sort(key=lambda a: order.get(a.severity, 3))
    return alerts
