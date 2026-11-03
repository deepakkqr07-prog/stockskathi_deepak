"""
Presentation Demo Mode Endpoints
"""

from fastapi import APIRouter, HTTPException
from backend.services.demo_service import demo_service

router = APIRouter(prefix="/api/demo", tags=["Demo Mode"])

@router.post("/seed")
def seed_demo_environment():
    try:
        return demo_service.seed_demo_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed demo data: {e}")

@router.post("/reset")
def reset_demo_environment():
    try:
        return demo_service.seed_demo_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset demo data: {e}")
