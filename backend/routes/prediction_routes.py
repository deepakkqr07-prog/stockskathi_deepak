"""
Demand Prediction API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any

from backend.services.prediction_service import prediction_service
from backend.services.subscription_service import subscription_service, Features
from backend.security import get_current_user

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])

@router.get("/")
def get_predictions(user: Dict[str, Any] = Depends(get_current_user)):
    if not subscription_service.can_access_feature(user, Features.DEMAND_PREDICTION):
        raise HTTPException(
            status_code=403,
            detail="AI Demand Prediction is a Premium feature. Upgrade or start your 3-day free trial."
        )
    return prediction_service.get_demand_predictions(str(user["_id"]))
