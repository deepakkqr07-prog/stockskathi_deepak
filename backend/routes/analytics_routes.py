"""
Analytics, Dead Money, Expiry Prevention & Daily Assistant API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any

from backend.services.analytics_service import analytics_service
from backend.services.subscription_service import subscription_service, Features
from backend.security import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/dead-money")
def get_dead_money(user: Dict[str, Any] = Depends(get_current_user)):
    if not subscription_service.can_access_feature(user, Features.DEAD_MONEY):
        raise HTTPException(
            status_code=403,
            detail="Dead Money Detector is a Premium feature. Upgrade or start your 3-day free trial."
        )
    return analytics_service.get_dead_money_report(str(user["_id"]))

@router.get("/expiry-prevention")
def get_expiry_prevention(user: Dict[str, Any] = Depends(get_current_user)):
    if not subscription_service.can_access_feature(user, Features.EXPIRY_PREVENTION):
        raise HTTPException(
            status_code=403,
            detail="Expiry Loss Prevention requires a Basic, Standard, or Premium plan."
        )
    return analytics_service.get_expiry_prevention_report(str(user["_id"]))

@router.get("/daily-assistant")
def get_daily_actions(user: Dict[str, Any] = Depends(get_current_user)):
    if not subscription_service.can_access_feature(user, Features.DAILY_ASSISTANT):
        raise HTTPException(
            status_code=403,
            detail="Daily Business Assistant requires a Basic, Standard, or Premium plan."
        )
    return analytics_service.get_daily_assistant_actions(str(user["_id"]))
