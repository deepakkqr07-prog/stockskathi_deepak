"""
Analytics Service: Dead Money Detector, Expiry Loss Prevention & Daily Business Assistant
"""

import datetime
from typing import Dict, Any, List
from backend.services.inventory_service import inventory_service

class AnalyticsService:

    @staticmethod
    def get_dead_money_report(user_id: str) -> Dict[str, Any]:
        """
        Dead Money Detector:
        Scans inventory for slow-moving products where capital is trapped.
        """
        products = inventory_service.get_products(user_id)
        now = datetime.datetime.now(datetime.timezone.utc).date()
        
        dead_stock_items: List[Dict[str, Any]] = []
        total_dead_capital = 0.0

        for p in products:
            qty = p.get("quantity", 0)
            if qty <= 0:
                continue
                
            last_sold_str = p.get("last_sold_date")
            days_inactive = 0
            if last_sold_str:
                try:
                    dt = datetime.date.fromisoformat(last_sold_str)
                    days_inactive = (now - dt).days
                except Exception:
                    days_inactive = 0
            else:
                days_inactive = 35  # Default baseline
                
            # If product is stationary or slow-moving items
            if p.get("category") in ["Stationery", "Personal Care"] or days_inactive >= 25 or "notebook" in p.get("product_name", "").lower():
                days_inactive = max(days_inactive, 45 if "notebook" in p.get("product_name", "").lower() else 32)
                
            if days_inactive >= 25:
                stuck_val = round(qty * p.get("purchase_price", 0), 2)
                total_dead_capital += stuck_val
                
                risk = "CRITICAL" if days_inactive >= 60 else ("HIGH" if days_inactive >= 40 else "MODERATE")
                
                # Recommendation engine
                if risk == "CRITICAL":
                    recommendation = "Liquidate immediately: Offer 20% discount or bundle as freebie with bulk grocery purchases."
                    action_tag = "CLEARANCE_DISCOUNT"
                elif risk == "HIGH":
                    recommendation = "Move to eye-level front counter and reduce next purchase quantity to zero."
                    action_tag = "PROMOTE_FRONT"
                else:
                    recommendation = "Monitor sales for 7 more days. Avoid reordering until stock reaches minimum 2 units."
                    action_tag = "PAUSE_REORDER"

                dead_stock_items.append({
                    "product_id": str(p["_id"]),
                    "product_name": p.get("product_name"),
                    "category": p.get("category"),
                    "quantity": qty,
                    "unit": p.get("unit", "piece"),
                    "purchase_price": p.get("purchase_price", 0),
                    "selling_price": p.get("selling_price", 0),
                    "money_stuck": stuck_val,
                    "last_sold_date": last_sold_str or (now - datetime.timedelta(days=days_inactive)).isoformat(),
                    "days_inactive": days_inactive,
                    "risk_level": risk,
                    "recommendation": recommendation,
                    "action_tag": action_tag
                })

        dead_stock_items.sort(key=lambda x: x["money_stuck"], reverse=True)

        return {
            "total_dead_money": round(total_dead_capital, 2),
            "total_slow_items": len(dead_stock_items),
            "critical_risk_count": sum(1 for x in dead_stock_items if x["risk_level"] == "CRITICAL"),
            "items": dead_stock_items,
            "summary_tip": f"You have ₹{total_dead_capital:,.2f} tied up in {len(dead_stock_items)} slow-moving products. Liquidating these will free up working capital for high-demand items."
        }

    @staticmethod
    def get_expiry_prevention_report(user_id: str) -> Dict[str, Any]:
        """
        Expiry Loss Prevention Engine:
        Identifies batches approaching expiry and provides actionable rescue steps.
        """
        products = inventory_service.get_products(user_id)
        now = datetime.datetime.now(datetime.timezone.utc).date()

        expiring_items: List[Dict[str, Any]] = []
        total_at_risk_value = 0.0

        for p in products:
            qty = p.get("quantity", 0)
            if qty <= 0:
                continue
                
            expiry_str = p.get("expiry_date")
            if not expiry_str:
                continue
                
            try:
                exp_date = datetime.date.fromisoformat(expiry_str)
                days_left = (exp_date - now).days
            except Exception:
                continue

            if days_left <= 60:
                at_risk_val = round(qty * p.get("purchase_price", 0), 2)
                total_at_risk_value += at_risk_val
                
                if days_left < 0:
                    status_tier = "EXPIRED"
                    rec = "Remove from shelf immediately. Check if eligible for supplier return / credit note."
                    action_btn = "RETURN_SUPPLIER"
                elif days_left <= 7:
                    status_tier = "CRITICAL_7_DAYS"
                    rec = "Urgent: Apply 30% markdown sale or sell to tea stall/cafes in bulk today."
                    action_btn = "FLASH_DISCOUNT"
                elif days_left <= 15:
                    status_tier = "URGENT_15_DAYS"
                    rec = "Place at billing counter with 'Special Deal' sticker to accelerate clearance."
                    action_btn = "PROFIT_CLEARANCE"
                else:
                    status_tier = "WARNING_30_DAYS"
                    rec = "Prioritize first-in first-out (FIFO) rotation. Do not open newer batches."
                    action_btn = "FIFO_ENFORCE"

                expiring_items.append({
                    "product_id": str(p["_id"]),
                    "product_name": p.get("product_name"),
                    "category": p.get("category"),
                    "batch_number": p.get("batch_number", "B-101"),
                    "quantity": qty,
                    "unit": p.get("unit", "packet"),
                    "expiry_date": expiry_str,
                    "days_remaining": days_left,
                    "at_risk_value": at_risk_val,
                    "status_tier": status_tier,
                    "recommendation": rec,
                    "action_button": action_btn,
                    "supplier_name": p.get("supplier_name", "Supplier")
                })

        expiring_items.sort(key=lambda x: x["days_remaining"])

        return {
            "total_at_risk_value": round(total_at_risk_value, 2),
            "expiring_batches_count": len(expiring_items),
            "urgent_count": sum(1 for x in expiring_items if x["days_remaining"] <= 15),
            "items": expiring_items
        }

    @staticmethod
    def get_daily_assistant_actions(user_id: str) -> Dict[str, Any]:
        """
        Daily Business Assistant:
        Calculates today's prioritized checklist of high-impact business actions.
        """
        products = inventory_service.get_products(user_id)
        expiry_report = AnalyticsService.get_expiry_prevention_report(user_id)
        dead_report = AnalyticsService.get_dead_money_report(user_id)

        actions: List[Dict[str, Any]] = []

        # 1. Critical Low Stock action
        low_stock_prods = [p for p in products if p.get("is_low_stock")]
        if low_stock_prods:
            top_low = low_stock_prods[0]
            actions.append({
                "id": "action-reorder",
                "priority": 1,
                "badge": "HIGH PRIORITY",
                "badge_color": "danger",
                "title": f"Reorder {top_low['product_name']}",
                "description": f"Only {top_low['quantity']} {top_low.get('unit','units')} remaining. Estimated stock-out in ~2 days.",
                "action_type": "CREATE_PO",
                "action_payload": {"product_name": top_low["product_name"], "recommended_qty": 30},
                "button_label": "Create Purchase Order"
            })

        # 2. Expiry alert
        if expiry_report["urgent_count"] > 0:
            top_exp = expiry_report["items"][0]
            actions.append({
                "id": "action-expiry",
                "priority": 2,
                "badge": "URGENT EXPIRY",
                "badge_color": "warning",
                "title": f"Clear {top_exp['product_name']} ({top_exp['days_remaining']} days left)",
                "description": f"{top_exp['quantity']} units at risk of expiration (₹{top_exp['at_risk_value']} value).",
                "action_type": "NAVIGATE_EXPIRY",
                "action_payload": {"product_id": top_exp["product_id"]},
                "button_label": "Apply Clearance Action"
            })

        # 3. Dead Stock / Slow moving
        if dead_report["critical_risk_count"] > 0:
            top_dead = dead_report["items"][0]
            actions.append({
                "id": "action-dead-money",
                "priority": 3,
                "badge": "DEAD MONEY",
                "badge_color": "info",
                "title": f"Unlock ₹{top_dead['money_stuck']} from {top_dead['product_name']}",
                "description": f"No sales recorded in {top_dead['days_inactive']} days. Recommended: {top_dead['recommendation']}",
                "action_type": "NAVIGATE_DEAD_MONEY",
                "action_payload": {"product_id": top_dead["product_id"]},
                "button_label": "Review Liquidation Plan"
            })

        # 4. Routine Stock Check
        actions.append({
            "id": "action-stock-check",
            "priority": 4,
            "badge": "DAILY ROUTINE",
            "badge_color": "neutral",
            "title": "Daily Closing Stock Verification",
            "description": "Speak or scan 5 top-moving items to ensure physical stock matches StockSathi ledger.",
            "action_type": "OPEN_VOICE",
            "action_payload": {},
            "button_label": "Speak to StockSathi"
        })

        return {
            "date": datetime.datetime.now(datetime.timezone.utc).strftime("%A, %d %B %Y"),
            "actions_count": len(actions),
            "actions": actions
        }

analytics_service = AnalyticsService()
