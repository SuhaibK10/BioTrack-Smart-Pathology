"""Pydantic schemas for request/response validation."""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class BiomarkerStatus(str, Enum):
    HIGH   = "HIGH"
    LOW    = "LOW"
    NORMAL = "NORMAL"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MODERATE = "moderate"


# ── Biomarker ────────────────────────────────────────────────────────────────

class BiomarkerResult(BaseModel):
    name:       str
    value:      float
    unit:       str
    ref_low:    Optional[float] = None
    ref_high:   Optional[float] = None
    ref_text:   str  = ""
    status:     BiomarkerStatus
    group:      str  = "General"


# ── Risk Assessment ──────────────────────────────────────────────────────────

class ShapEntry(BaseModel):
    feature: str
    impact:  float
    positive: bool


class RiskResult(BaseModel):
    category:   str
    score:      float           # 0.0 – 1.0
    label:      str             # e.g. "High Risk"
    shap:       List[ShapEntry] = []


# ── Alert ────────────────────────────────────────────────────────────────────

class AlertItem(BaseModel):
    severity:   AlertSeverity
    title:      str
    detail:     str
    system:     str
    marker:     str
    value:      float
    unit:       str


# ── Advisory ─────────────────────────────────────────────────────────────────

class AdvisorySection(BaseModel):
    icon:   str
    tag:    str
    key:    str
    values: str
    color:  str
    recs:   List[str]


class Advisory(BaseModel):
    summary:   str
    sections:  List[AdvisorySection]


# ── System Health ────────────────────────────────────────────────────────────

class SystemHealth(BaseModel):
    name:   str
    score:  int
    flags:  int
    color:  str


# ── Patient ──────────────────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    name:      str
    age:       int
    sex:       str
    clinic_id: Optional[str] = None


class Patient(PatientCreate):
    id:         str
    created_at: datetime


# ── Report Upload Response ────────────────────────────────────────────────────

class ReportAnalysis(BaseModel):
    patient:         Optional[dict]      = None
    lab_name:        str                 = ""
    report_date:     str                 = ""
    patient_id_lab:  str                 = ""
    biomarkers:      List[BiomarkerResult]
    abnormal:        List[BiomarkerResult]
    alerts:          List[AlertItem]
    risk_scores:     List[RiskResult]
    system_health:   List[SystemHealth]
    advisory:        Advisory
    stats: dict = Field(default_factory=lambda: {
        "total": 0, "abnormal": 0, "critical_flags": 0, "systems_reviewed": 8
    })
