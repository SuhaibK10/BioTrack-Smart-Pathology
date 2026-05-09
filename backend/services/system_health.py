"""
System Health Scorer
--------------------
Computes a 0–100 health score for 8 organ systems based on
biomarker deviations within each system.
"""

from typing import List
from models.schemas import BiomarkerResult, SystemHealth, BiomarkerStatus

SYSTEMS = {
    "Haematology":   (["Hemoglobin","RBC","HCT","MCH","RDW-CV","MPV","PDW","Platelet Count","WBC"],  "#FF4060"),
    "Inflammatory":  (["ESR","CRP"],                                                                   "#FF4060"),
    "Thyroid":       (["TSH","T3","T4"],                                                               "#FFB020"),
    "Renal":         (["Creatinine","BUN","Urea","Uric Acid","UACR","Microalbumin","Sodium","Chloride"],"#FFB020"),
    "Vitamins":      (["Vitamin D","Folate","Vitamin B12","Calcium"],                                  "#FFB020"),
    "Lipids":        (["Total Cholesterol","Triglycerides","HDL","LDL","VLDL"],                        "#4D9EFF"),
    "Liver":         (["SGOT","SGPT","ALP","GGT","Albumin","Bilirubin Total","Total Protein"],         "#00D4AA"),
    "Diabetes":      (["Fasting Glucose","HbA1c"],                                                     "#00D4AA"),
}


def compute(biomarkers: List[BiomarkerResult]) -> List[SystemHealth]:
    bm_map = {b.name: b for b in biomarkers}
    results = []

    for system_name, (markers, color) in SYSTEMS.items():
        present     = [bm_map[m] for m in markers if m in bm_map]
        flags       = sum(1 for b in present if b.status != BiomarkerStatus.NORMAL)
        total       = len(present)

        if total == 0:
            score = 75  # no data — neutral
        else:
            # Base: start at 100, subtract for each abnormal
            # Weight HIGH/LOW differently (severity penalty)
            penalty = 0
            for b in present:
                if b.status == BiomarkerStatus.NORMAL:
                    continue
                # How far out of range?
                if b.status == BiomarkerStatus.HIGH and b.ref_high and b.ref_high > 0:
                    ratio = (b.value - b.ref_high) / b.ref_high
                elif b.status == BiomarkerStatus.LOW and b.ref_low and b.ref_low > 0:
                    ratio = (b.ref_low - b.value) / b.ref_low
                else:
                    ratio = 0.2
                penalty += min(ratio * 40, 25)  # cap per marker

            score = max(0, min(100, round(100 - penalty)))

        results.append(SystemHealth(
            name=system_name,
            score=score,
            flags=flags,
            color=color,
        ))

    return results
