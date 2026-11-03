"""
Supplier API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from backend.services.supplier_service import supplier_service
from backend.services.subscription_service import subscription_service, Features
from backend.security import get_current_user

router = APIRouter(prefix="/api/suppliers", tags=["Suppliers"])

class SupplierCreateRequest(BaseModel):
    name: str
    contact_person: Optional[str] = "Manager"
    phone: Optional[str] = ""
    email: Optional[str] = ""
    address: Optional[str] = "Mandi"
    categories: Optional[List[str]] = ["Groceries"]
    delivery_time_days: Optional[int] = 1
    reliability_score: Optional[int] = 95
    min_order_amount: Optional[float] = 1000.0
    payment_terms: Optional[str] = "Net 7 Days Credit"

class SupplierCompareRequest(BaseModel):
    product_name: str
    required_quantity: int = 50

@router.get("/")
def list_suppliers(user: Dict[str, Any] = Depends(get_current_user)):
    return supplier_service.get_suppliers(str(user["_id"]))

@router.post("/")
def create_supplier(payload: SupplierCreateRequest, user: Dict[str, Any] = Depends(get_current_user)):
    try:
        return supplier_service.create_supplier(str(user["_id"]), payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/compare")
def compare_suppliers(payload: SupplierCompareRequest, user: Dict[str, Any] = Depends(get_current_user)):
    if not subscription_service.can_access_feature(user, Features.SUPPLIER_COMPARISON):
        raise HTTPException(
            status_code=403,
            detail="Smart Supplier Comparison is a Premium feature. Upgrade or start your 3-day free trial."
        )
    return supplier_service.compare_suppliers_for_product(
        str(user["_id"]), payload.product_name, payload.required_quantity
    )
