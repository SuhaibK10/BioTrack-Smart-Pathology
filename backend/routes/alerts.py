"""Alerts router."""
from fastapi import APIRouter
router = APIRouter()

@router.get("/")
def list_alerts():
    return {"alerts": [], "message": "Connect Supabase to see live alerts"}
