"""
Inventory and Product API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from backend.services.inventory_service import inventory_service
from backend.security import get_current_user

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])

class ProductCreateRequest(BaseModel):
    product_name: str
    category: str = "Groceries"
    quantity: int = 0
    unit: str = "packet"
    purchase_price: float = 0.0
    selling_price: float = 0.0
    supplier_name: Optional[str] = "Local Supplier"
    supplier_id: Optional[str] = None
    min_stock_level: int = 10
    expiry_date: Optional[str] = None
    batch_number: Optional[str] = None
    last_sold_date: Optional[str] = None
    monthly_sales_avg: Optional[int] = 30

class ProductUpdateRequest(BaseModel):
    product_name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    purchase_price: Optional[float] = None
    selling_price: Optional[float] = None
    supplier_name: Optional[str] = None
    min_stock_level: Optional[int] = None
    expiry_date: Optional[str] = None
    batch_number: Optional[str] = None
    last_sold_date: Optional[str] = None
    monthly_sales_avg: Optional[int] = None

class StockAdjustRequest(BaseModel):
    product_name_or_id: str
    delta: Optional[int] = None
    exact_quantity: Optional[int] = None
    reason: str = "Manual adjustment"

@router.get("/products")
def list_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    filter_type: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    return inventory_service.get_products(str(user["_id"]), search, category, filter_type)

@router.get("/products/{product_id}")
def get_product_detail(product_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    prod = inventory_service.get_product(str(user["_id"]), product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found.")
    return prod

@router.post("/products")
def add_product(payload: ProductCreateRequest, user: Dict[str, Any] = Depends(get_current_user)):
    try:
        return inventory_service.create_product(str(user["_id"]), payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/products/{product_id}")
def update_product_info(product_id: str, payload: ProductUpdateRequest, user: Dict[str, Any] = Depends(get_current_user)):
    try:
        return inventory_service.update_product(str(user["_id"]), product_id, payload.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/products/{product_id}")
def delete_product_item(product_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    success = inventory_service.delete_product(str(user["_id"]), product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found.")
    return {"success": True, "message": "Product removed from inventory."}

@router.patch("/adjust-stock")
def adjust_product_stock(payload: StockAdjustRequest, user: Dict[str, Any] = Depends(get_current_user)):
    try:
        return inventory_service.adjust_stock(
            user_id=str(user["_id"]),
            product_name_or_id=payload.product_name_or_id,
            delta=payload.delta,
            exact_qty=payload.exact_quantity,
            reason=payload.reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/kpis")
def get_kpis(user: Dict[str, Any] = Depends(get_current_user)):
    return inventory_service.get_dashboard_kpis(str(user["_id"]))
