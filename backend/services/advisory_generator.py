"""
Advisory Generator
------------------
Generates a physician-grade clinical advisory using Google Gemini.
Falls back to a template-based advisory if API key is not configured.
"""

import os
import json
import logging
from typing import List

from models.schemas import (
    BiomarkerResult, RiskResult, AlertItem, Advisory,
    AdvisorySection, BiomarkerStatus
)

logger = logging.getLogger(__name__)


# ── Template fallback ────────────────────────────────────────────────────────

SECTION_TEMPLATES = {
    "Iron-Deficiency Anaemia": AdvisorySection(
        icon="🔴", tag="Priority 1 · Haematology",
        key="Iron-Deficiency Anaemia", color="#FF4060",
        values="Hb ↓ · Iron ↓ · Transferrin saturation ↓",
        recs=[
            "Start oral iron: Ferrous sulphate 200 mg TDS with Vitamin C on empty stomach",
            "Investigate aetiology: dietary deficiency vs occult GI blood loss",
            "Repeat CBC + iron studies in 8 weeks to confirm response",
        ],
    ),
    "Systemic Inflammation": AdvisorySection(
        icon="🔴", tag="Priority 1 · Inflammatory",
        key="Systemic Inflammation", color="#FF4060",
        values="ESR ↑ · CRP ↑",
        recs=[
            "Differential: bacterial infection, TB, autoimmune disease, haematological malignancy",
            "Clinical correlation with symptoms essential; consider ANA, ANCA, TB screening",
            "Re-check both markers at 6-week follow-up; residual elevation requires urgent workup",
        ],
    ),
    "Thyroid Dysfunction": AdvisorySection(
        icon="🔴", tag="Priority 1 · Thyroid",
        key="Subclinical/Clinical Hypothyroidism", color="#FF4060",
        values="TSH ↑ · T3/T4 may be normal",
        recs=[
            "Endocrinology referral for levothyroxine initiation assessment",
            "Repeat TFT with Free T3 & Free T4 in 6–8 weeks to confirm trend",
            "Note: hypothyroidism worsens anaemia, raises LDL, and impairs cognition",
        ],
    ),
    "Renal Involvement": AdvisorySection(
        icon="🟠", tag="Priority 2 · Renal",
        key="Renal Function Concern", color="#FFB020",
        values="BUN ↑ / Creatinine ↑ / UACR ↑",
        recs=[
            "Confirm microalbuminuria with 2 further morning urines within 3–6 months (ADA 2024)",
            "Target BP < 130/80 mmHg; consider ACE inhibitor or ARB if not contraindicated",
            "Ensure adequate hydration; avoid NSAIDs and nephrotoxic agents",
        ],
    ),
    "Vitamin & Folate Deficiency": AdvisorySection(
        icon="🔵", tag="Priority 3 · Vitamins",
        key="Vitamin D & Folate Deficiency", color="#4D9EFF",
        values="Vitamin D ↓ · Folate ↓",
        recs=[
            "Cholecalciferol 60,000 IU weekly × 8 weeks, then 1000–2000 IU/day maintenance",
            "Folic acid 5 mg OD × 4 months; recheck levels at completion",
            "DEXA scan recommended in elderly patients with severe Vitamin D deficiency",
        ],
    ),
}


def _template_advisory(
    biomarkers: List[BiomarkerResult],
    risks: List[RiskResult],
    alerts: List[AlertItem],
) -> Advisory:
    """Generate advisory from static templates filtered by detected risks."""
    sections: List[AdvisorySection] = []
    for risk in sorted(risks, key=lambda r: r.score, reverse=True):
        if risk.score >= 0.25 and risk.category in SECTION_TEMPLATES:
            sections.append(SECTION_TEMPLATES[risk.category])

    abnormal = [b for b in biomarkers if b.status != BiomarkerStatus.NORMAL]
    abn_text = ", ".join(
        f"{b.name} {b.value} {b.unit} ({'↑' if b.status == BiomarkerStatus.HIGH else '↓'})"
        for b in abnormal[:8]
    )

    summary = (
        f"This patient presents with {len(abnormal)} abnormal biomarkers "
        f"across multiple organ systems. Key findings include: {abn_text}. "
        "The AI risk model has identified the conditions detailed below. "
        "All findings require clinical correlation and physician review before action."
    )

    return Advisory(summary=summary, sections=sections)


# ── Gemini advisory ──────────────────────────────────────────────────────────

def _gemini_advisory(
    biomarkers: List[BiomarkerResult],
    risks: List[RiskResult],
    patient_context: dict,
) -> Advisory:
    """Call Gemini API and parse structured advisory."""
    import google.generativeai as genai

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not configured")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro-latest")

    abnormal = [b for b in biomarkers if b.status != BiomarkerStatus.NORMAL]
    abn_lines = "\n".join(
        f"  - {b.name}: {b.value} {b.unit} "
        f"(ref {b.ref_low}–{b.ref_high}, status: {b.status.value})"
        for b in abnormal
    )
    risk_lines = "\n".join(
        f"  - {r.category}: {r.score*100:.0f}% ({r.label})"
        for r in risks
    )

    prompt = f"""
You are a senior clinical pathologist reviewing a lab report.

PATIENT: {patient_context.get('name', 'Unknown')}, 
Age {patient_context.get('age', '?')} {patient_context.get('sex', '')}

ABNORMAL BIOMARKERS:
{abn_lines}

AI RISK SCORES:
{risk_lines}

Generate a clinical advisory in the following JSON format:
{{
  "summary": "<2–3 sentence clinical narrative summary>",
  "sections": [
    {{
      "icon": "<emoji>",
      "tag": "<Priority level and system>",
      "key": "<finding name>",
      "values": "<key abnormal values>",
      "color": "<hex color: use #FF4060 for critical, #FFB020 for moderate, #4D9EFF for low>",
      "recs": ["<rec 1>", "<rec 2>", "<rec 3>"]
    }}
  ]
}}

Rules:
- Include only findings with clinical significance
- Each section has exactly 3 evidence-based recommendations
- Use specific drug names, doses, and monitoring intervals
- Reference ADA 2024, BTA, ICMR guidelines where appropriate
- Return ONLY valid JSON, no markdown
"""

    response = model.generate_content(prompt)
    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    data = json.loads(raw)
    sections = [AdvisorySection(**s) for s in data.get("sections", [])]
    return Advisory(summary=data.get("summary", ""), sections=sections)


# ── Public API ───────────────────────────────────────────────────────────────

def generate(
    biomarkers: List[BiomarkerResult],
    risks: List[RiskResult],
    alerts: List[AlertItem],
    patient_context: dict | None = None,
) -> Advisory:
    """
    Generate a clinical advisory.
    Uses Gemini if API key is configured, otherwise uses template.
    """
    ctx = patient_context or {}
    try:
        return _gemini_advisory(biomarkers, risks, ctx)
    except Exception as e:
        logger.warning(f"Gemini advisory failed ({e}), using template fallback")
        return _template_advisory(biomarkers, risks, alerts)
