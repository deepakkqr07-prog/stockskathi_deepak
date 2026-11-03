"""
Voice AI API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, Dict, Any

from backend.services.voice_service import voice_service
from backend.services.subscription_service import subscription_service, Features
from backend.security import get_current_user

router = APIRouter(prefix="/api/voice", tags=["Voice AI"])

class VoiceParseRequest(BaseModel):
    transcript: str
    language: Optional[str] = "Hindi"
    existing_context: Optional[Dict[str, Any]] = None

class VoiceConfirmRequest(BaseModel):
    pending_action: Dict[str, Any]
    language: Optional[str] = "Hindi"

@router.post("/parse")
def parse_voice_transcript(payload: VoiceParseRequest, user: Dict[str, Any] = Depends(get_current_user)):
    if not subscription_service.can_access_feature(user, Features.VOICE_AI):
        raise HTTPException(
            status_code=403,
            detail="Voice AI Assistant is a Premium feature. Upgrade or start your 3-day free trial."
        )
    return voice_service.parse_command(
        user_id=str(user["_id"]),
        transcript=payload.transcript,
        language=payload.language or "Hindi",
        existing_context=payload.existing_context
    )

@router.post("/confirm")
def execute_voice_confirmation(payload: VoiceConfirmRequest, user: Dict[str, Any] = Depends(get_current_user)):
    if not subscription_service.can_access_feature(user, Features.VOICE_AI):
        raise HTTPException(
            status_code=403,
            detail="Voice AI Assistant is a Premium feature."
        )
    try:
        return voice_service.execute_confirmed_action(
            user_id=str(user["_id"]),
            pending_action=payload.pending_action,
            language=payload.language or "Hindi"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
