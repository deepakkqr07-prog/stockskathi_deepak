"""
Subscription, Trial, and Checkout API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, Dict, Any

from backend.services.subscription_service import subscription_service, PLANS
from backend.security import get_current_user

router = APIRouter(prefix="/api/subscription", tags=["Subscription"])

class CheckoutRequest(BaseModel):
    plan_name: str
    payment_method: str = "UPI"
    billing_cycle: str = "monthly"

@router.get("/plans")
def get_plans():
    return PLANS

@router.get("/status")
def get_status(user: Dict[str, Any] = Depends(get_current_user)):
    return subscription_service.get_user_subscription_status(user)

@router.post("/start-trial")
def start_free_trial(user: Dict[str, Any] = Depends(get_current_user)):
    try:
        return subscription_service.start_free_trial(str(user["_id"]))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/checkout")
def process_checkout(payload: CheckoutRequest, user: Dict[str, Any] = Depends(get_current_user)):
    try:
        return subscription_service.process_subscription_checkout(
            user_id=str(user["_id"]),
            plan_name=payload.plan_name,
            payment_method=payload.payment_method,
            billing_cycle=payload.billing_cycle
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
