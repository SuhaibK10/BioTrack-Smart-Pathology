"""Patients router — CRUD operations."""
from fastapi import APIRouter
from models.schemas import PatientCreate

router = APIRouter()

@router.get("/")
def list_patients():
    return {"patients": [], "message": "Connect Supabase to see patients"}

@router.post("/")
def create_patient(data: PatientCreate):
    return {"id": "demo-id", **data.model_dump()}
