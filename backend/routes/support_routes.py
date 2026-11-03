"""
AI Support Assistant API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, Dict, Any

from backend.services.support_service import support_service
from backend.services.subscription_service import subscription_service, Features
from backend.security import get_current_user

router = APIRouter(prefix="/api/support", tags=["Support"])

class SupportQueryRequest(BaseModel):
    message: str
    language: Optional[str] = "Hindi"

@router.post("/chat")
def chat_with_assistant(payload: SupportQueryRequest, user: Dict[str, Any] = Depends(get_current_user)):
    if not subscription_service.can_access_feature(user, Features.AI_SUPPORT):
        raise HTTPException(
            status_code=403,
            detail="StockSathi AI Support Assistant is a Premium feature. Upgrade or start your 3-day free trial."
        )
    return support_service.answer_query(
        user_id=str(user["_id"]),
        message=payload.message,
        language=payload.language or "Hindi"
    )
