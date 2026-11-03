"""
Inventory and Product Management Service
"""

import datetime
from typing import Dict, Any, List, Optional
from backend.database import get_db_collection

class InventoryService:

    @staticmethod
    def get_products(user_id: str, search: Optional[str] = None, category: Optional[str] = None, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        products_coll = get_db_collection("products")
        query: Dict[str, Any] = {"user_id": user_id}
        
        if category and category != "ALL":
            query["category"] = category
            
        products = products_coll.find(query, sort=[("product_name", 1)])
        
        if search:
            s = search.lower().strip()
            products = [
                p for p in products 
                if s in p.get("product_name", "").lower() or s in p.get("category", "").lower() or s in p.get("supplier_name", "").lower()
            ]

        # Calculate dynamic status
        now = datetime.datetime.now(datetime.timezone.utc).date()
        for p in products:
            qty = p.get("quantity", 0)
            min_lvl = p.get("min_stock_level", 10)
            expiry_str = p.get("expiry_date")
            
            p["is_low_stock"] = qty <= min_lvl
            p["is_out_of_stock"] = qty == 0
            
            p["days_to_expiry"] = None
            p["is_expiring_soon"] = False
            p["is_expired"] = False
            
            if expiry_str:
                try:
                    exp_date = datetime.date.fromisoformat(expiry_str)
                    days = (exp_date - now).days
                    p["days_to_expiry"] = days
                    if days < 0:
                        p["is_expired"] = True
                    elif days <= 30:
                        p["is_expiring_soon"] = True
                except Exception:
                    pass
                    
            # Stock value
            p["stock_value"] = round(qty * p.get("purchase_price", 0), 2)
            p["retail_value"] = round(qty * p.get("selling_price", 0), 2)

        if filter_type == "low_stock":
            products = [p for p in products if p.get("is_low_stock")]
        elif filter_type == "expiring":
            products = [p for p in products if p.get("is_expiring_soon") or p.get("is_expired")]
        elif filter_type == "out_of_stock":
            products = [p for p in products if p.get("is_out_of_stock")]
            
        return products

    @staticmethod
    def get_product(user_id: str, product_id: str) -> Optional[Dict[str, Any]]:
        products_coll = get_db_collection("products")
        return products_coll.find_one({"_id": product_id, "user_id": user_id})

    @staticmethod
    def create_product(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        products_coll = get_db_collection("products")
        
        name = data.get("product_name", "").strip()
        if not name:
            raise ValueError("Product name is required.")
            
        now = datetime.datetime.now(datetime.timezone.utc)
        
        product_doc = {
            "user_id": user_id,
            "product_name": name,
            "category": data.get("category", "Groceries"),
            "quantity": int(data.get("quantity", 0)),
            "unit": data.get("unit", "packet"),
            "purchase_price": float(data.get("purchase_price", 0)),
            "selling_price": float(data.get("selling_price", 0)),
            "supplier_name": data.get("supplier_name", "Local Vendor"),
            "supplier_id": data.get("supplier_id"),
            "min_stock_level": int(data.get("min_stock_level", 10)),
            "expiry_date": data.get("expiry_date"),
            "batch_number": data.get("batch_number", "BATCH-01"),
            "last_sold_date": data.get("last_sold_date", now.date().isoformat()),
            "monthly_sales_avg": int(data.get("monthly_sales_avg", 30)),
            "created_at": now.isoformat()
        }
        
        res = products_coll.insert_one(product_doc)
        product_doc["_id"] = str(res.inserted_id)
        
        # Check if low stock notification needed
        if product_doc["quantity"] <= product_doc["min_stock_level"]:
            notifs = get_db_collection("notifications")
            notifs.insert_one({
                "user_id": user_id,
                "type": "LOW_STOCK",
                "title": f"⚠️ Low Stock Alert: {name}",
                "message": f"Stock is currently {product_doc['quantity']} {product_doc['unit']}s (Minimum: {product_doc['min_stock_level']}).",
                "is_read": False
            })
            
        return product_doc

    @staticmethod
    def update_product(user_id: str, product_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        products_coll = get_db_collection("products")
        existing = products_coll.find_one({"_id": product_id, "user_id": user_id})
        if not existing:
            raise ValueError("Product not found.")
            
        update_fields = {}
        for key in ["product_name", "category", "unit", "supplier_name", "supplier_id", "expiry_date", "batch_number", "last_sold_date"]:
            if key in data:
                update_fields[key] = data[key]
                
        if "quantity" in data:
            update_fields["quantity"] = int(data["quantity"])
        if "purchase_price" in data:
            update_fields["purchase_price"] = float(data["purchase_price"])
        if "selling_price" in data:
            update_fields["selling_price"] = float(data["selling_price"])
        if "min_stock_level" in data:
            update_fields["min_stock_level"] = int(data["min_stock_level"])
        if "monthly_sales_avg" in data:
            update_fields["monthly_sales_avg"] = int(data["monthly_sales_avg"])
            
        products_coll.update_one({"_id": product_id, "user_id": user_id}, {"$set": update_fields})
        return products_coll.find_one({"_id": product_id, "user_id": user_id})

    @staticmethod
    def delete_product(user_id: str, product_id: str) -> bool:
        products_coll = get_db_collection("products")
        res = products_coll.delete_one({"_id": product_id, "user_id": user_id})
        return res.deleted_count > 0

    @staticmethod
    def adjust_stock(user_id: str, product_name_or_id: str, delta: Optional[int] = None, exact_qty: Optional[int] = None, reason: str = "Manual Adjustment") -> Dict[str, Any]:
        products_coll = get_db_collection("products")
        
        # Match by ID or exact/case-insensitive name
        product = products_coll.find_one({
            "user_id": user_id,
            "_id": product_name_or_id
        })
        
        if not product:
            # Try fuzzy match name
            all_prods = products_coll.find({"user_id": user_id})
            target_name = product_name_or_id.lower().strip()
            for p in all_prods:
                if p["product_name"].lower() == target_name or target_name in p["product_name"].lower():
                    product = p
                    break
                    
        if not product:
            raise ValueError(f"Product '{product_name_or_id}' was not found in your inventory.")
            
        prev_qty = product.get("quantity", 0)
        if exact_qty is not None:
            new_qty = max(0, exact_qty)
        elif delta is not None:
            new_qty = max(0, prev_qty + delta)
        else:
            new_qty = prev_qty
            
        products_coll.update_one(
            {"_id": product["_id"]},
            {"$set": {
                "quantity": new_qty,
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }}
        )
        
        # Log stock ledger
        ledger_coll = get_db_collection("stock_ledger")
        ledger_coll.insert_one({
            "user_id": user_id,
            "product_id": str(product["_id"]),
            "product_name": product["product_name"],
            "previous_quantity": prev_qty,
            "change": new_qty - prev_qty,
            "new_quantity": new_qty,
            "reason": reason,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })
        
        return {
            "product_id": str(product["_id"]),
            "product_name": product["product_name"],
            "previous_quantity": prev_qty,
            "change": new_qty - prev_qty,
            "new_quantity": new_qty,
            "unit": product.get("unit", "packet"),
            "message": f"Successfully updated {product['product_name']} stock to {new_qty} {product.get('unit', 'packet')}s."
        }

    @staticmethod
    def get_dashboard_kpis(user_id: str) -> Dict[str, Any]:
        products = InventoryService.get_products(user_id)
        
        total_products = len(products)
        total_stock_value = sum(p["stock_value"] for p in products)
        total_retail_value = sum(p["retail_value"] for p in products)
        low_stock_count = sum(1 for p in products if p.get("is_low_stock"))
        expiring_count = sum(1 for p in products if p.get("is_expiring_soon") or p.get("is_expired"))
        
        # Dead stock calculation: products with last_sold_date > 30 days ago
        now = datetime.datetime.now(datetime.timezone.utc).date()
        dead_stock_value = 0
        dead_stock_count = 0
        for p in products:
            last_sold = p.get("last_sold_date")
            if last_sold:
                try:
                    dt = datetime.date.fromisoformat(last_sold)
                    if (now - dt).days >= 30 and p.get("quantity", 0) > 0:
                        dead_stock_value += p["stock_value"]
                        dead_stock_count += 1
                except Exception:
                    pass

        return {
            "total_products": total_products,
            "total_stock_value": round(total_stock_value, 2),
            "total_retail_value": round(total_retail_value, 2),
            "low_stock_count": low_stock_count,
            "expiring_soon_count": expiring_count,
            "dead_stock_value": round(dead_stock_value, 2),
            "dead_stock_count": dead_stock_count
        }

inventory_service = InventoryService()
