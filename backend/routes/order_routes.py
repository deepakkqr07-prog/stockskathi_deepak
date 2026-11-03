"""
Purchase Order API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from backend.services.order_service import order_service
from backend.services.subscription_service import subscription_service, Features
from backend.security import get_current_user

router = APIRouter(prefix="/api/orders", tags=["Orders"])

class OrderItem(BaseModel):
    product_name: str
    quantity: int
    unit_price: float
    unit: Optional[str] = "packet"

class OrderCreateRequest(BaseModel):
    supplier_name: str
    supplier_phone: Optional[str] = ""
    items: List[OrderItem]
    delivery_days: Optional[int] = 1
    notes: Optional[str] = "Generated via StockSathi"
    source: Optional[str] = "MANUAL"

class OrderStatusUpdate(BaseModel):
    status: str

@router.get("/")
def list_orders(status_filter: Optional[str] = None, user: Dict[str, Any] = Depends(get_current_user)):
    return order_service.get_orders(str(user["_id"]), status_filter)

@router.post("/")
def create_purchase_order(payload: OrderCreateRequest, user: Dict[str, Any] = Depends(get_current_user)):
    if not subscription_service.can_access_feature(user, Features.PURCHASE_ACTIONS):
        raise HTTPException(
            status_code=403,
            detail="Automated Purchase Orders require a Standard or Premium plan."
        )
    try:
        return order_service.create_order(str(user["_id"]), payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{order_id}/status")
def update_status(order_id: str, payload: OrderStatusUpdate, user: Dict[str, Any] = Depends(get_current_user)):
    try:
        return order_service.update_order_status(str(user["_id"]), order_id, payload.status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
