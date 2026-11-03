"""
Purchase Order Management Service
Handles PO creation from AI recommendations, supplier dispatch, and automated stock receipt.
"""

import datetime
from typing import Dict, Any, List, Optional
from backend.database import get_db_collection
from backend.services.inventory_service import inventory_service

class OrderService:

    @staticmethod
    def get_orders(user_id: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        orders_coll = get_db_collection("purchase_orders")
        query: Dict[str, Any] = {"user_id": user_id}
        if status_filter and status_filter != "ALL":
            query["status"] = status_filter
            
        return orders_coll.find(query, sort=[("created_at", -1)])

    @staticmethod
    def create_order(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        orders_coll = get_db_collection("purchase_orders")
        now = datetime.datetime.now(datetime.timezone.utc)
        
        items = data.get("items", [])
        if not items:
            raise ValueError("Purchase order must contain at least one product item.")
            
        total_amount = sum(float(it.get("unit_price", 0)) * int(it.get("quantity", 0)) for it in items)
        
        order_count = orders_coll.count_documents({"user_id": user_id}) + 1
        po_number = f"PO-{now.strftime('%Y%m')}-{order_count:04d}"
        
        expected_delivery = (now + datetime.timedelta(days=int(data.get("delivery_days", 1)))).date().isoformat()
        
        po_doc = {
            "user_id": user_id,
            "po_number": po_number,
            "supplier_name": data.get("supplier_name", "Primary Distributor"),
            "supplier_phone": data.get("supplier_phone", "+91 98101 23456"),
            "items": items,
            "total_amount": round(total_amount, 2),
            "status": data.get("status", "PLACED"),
            "notes": data.get("notes", "Auto-generated via StockSathi Recommendation Engine"),
            "created_at": now.isoformat(),
            "expected_delivery": expected_delivery,
            "source": data.get("source", "RECOMMENDATION_ENGINE")
        }
        
        res = orders_coll.insert_one(po_doc)
        po_doc["_id"] = str(res.inserted_id)
        
        # Log notification
        notifs = get_db_collection("notifications")
        notifs.insert_one({
            "user_id": user_id,
            "type": "PO_CREATED",
            "title": f"📋 Purchase Order Generated: {po_number}",
            "message": f"Order for {len(items)} items placed with {po_doc['supplier_name']} (Total: ₹{total_amount:,.2f}).",
            "is_read": False
        })
        
        return po_doc

    @staticmethod
    def update_order_status(user_id: str, order_id: str, new_status: str) -> Dict[str, Any]:
        orders_coll = get_db_collection("purchase_orders")
        order = orders_coll.find_one({"_id": order_id, "user_id": user_id})
        if not order:
            raise ValueError("Purchase order not found.")
            
        orders_coll.update_one(
            {"_id": order_id, "user_id": user_id},
            {"$set": {
                "status": new_status,
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }}
        )
        
        # If status changed to RECEIVED, auto-update stock in inventory
        if new_status == "RECEIVED" and order.get("status") != "RECEIVED":
            for item in order.get("items", []):
                p_name = item.get("product_name")
                qty = int(item.get("quantity", 0))
                try:
                    inventory_service.adjust_stock(
                        user_id=user_id,
                        product_name_or_id=p_name,
                        delta=qty,
                        reason=f"Received against {order.get('po_number', 'PO')}"
                    )
                except Exception as e:
                    print(f"[OrderService] Could not auto-adjust stock for {p_name}: {e}")

        return orders_coll.find_one({"_id": order_id, "user_id": user_id})

order_service = OrderService()
