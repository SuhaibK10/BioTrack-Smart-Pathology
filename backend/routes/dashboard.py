"""Dashboard summary router."""
from fastapi import APIRouter
router = APIRouter()

@router.get("/summary")
def summary():
    return {
        "total_reports": 1,
        "total_patients": 1,
        "critical_alerts": 3,
        "message": "Connect Supabase for live data",
    }
