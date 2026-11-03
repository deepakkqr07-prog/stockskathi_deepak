"""
AI Support Assistant Service
Provides contextual, grounded business and inventory assistance for shopkeepers.
Uses live database facts and enforces confirmation safeguards for write actions.
"""

import re
import datetime
from typing import Dict, Any, List, Optional
from backend.services.inventory_service import inventory_service
from backend.services.analytics_service import analytics_service
from backend.services.prediction_service import prediction_service
from backend.services.supplier_service import supplier_service
from backend.services.voice_service import voice_service

class SupportService:

    @staticmethod
    def answer_query(user_id: str, message: str, language: str = "Hindi") -> Dict[str, Any]:
        msg_clean = message.strip()
        msg_lower = msg_clean.lower()

        # Check if user is asking to mutate data (Safety check)
        if any(w in msg_lower for w in ["stock update", "add kar", "kam kar", "set kar", "badha do", "change stock"]):
            # Route through voice intent parser to generate confirmation safety card
            voice_parsed = voice_service.parse_command(user_id, msg_clean, language)
            if voice_parsed.get("status") == "CONFIRMATION_REQUIRED":
                action = voice_parsed["pending_action"]
                return {
                    "reply": f"Main {action['product_name']} ka stock update kar sakta hoon. Current stock {action['current_stock']} hai aur new stock {action['new_stock']} ho jayega. Kya aap ise confirm karte hain?",
                    "action_required": True,
                    "pending_action": action,
                    "grounded_sources": ["Inventory Ledger"]
                }

        # Fetch actual live shop state
        kpis = inventory_service.get_dashboard_kpis(user_id)
        products = inventory_service.get_products(user_id)

        # 1. Total stock value / inventory worth
        if any(w in msg_lower for w in ["stock value", "kul maal", "total value", "kitne ka maal", "total stock", "worth"]):
            reply = (
                f"Aapki dukaan ka kul stock value **₹{kpis['total_stock_value']:,.2f}** hai (purchase price par). "
                f"Iska selling retail value lagbhag **₹{kpis['total_retail_value']:,.2f}** hai. "
                f"Dukaan mein kul **{kpis['total_products']} products** registered hain."
            )
            return {"reply": reply, "grounded_sources": ["Live Inventory Value", "KPI Summary"]}

        # 2. Today's business actions / Aaj kya karein
        if any(w in msg_lower for w in ["aaj kya", "kya karna chahiye", "today", "actions", "recommendation", "priority"]):
            daily = analytics_service.get_daily_assistant_actions(user_id)
            action_lines = []
            for idx, act in enumerate(daily["actions"][:3], 1):
                action_lines.append(f"{idx}. **{act['title']}**: {act['description']}")
            
            reply = (
                f"**Aaj ke mukhya business actions ({daily['date']}):**\n\n" + 
                "\n".join(action_lines) +
                "\n\nAap kisi bhi action ko dashboard ya voice se seedhe execute kar sakte hain."
            )
            return {"reply": reply, "grounded_sources": ["Daily Business Engine", "Stock Analytics"]}

        # 3. Low stock items
        if any(w in msg_lower for w in ["low stock", "kam stock", "khatam", "out of stock", "reorder"]):
            low_items = [p for p in products if p.get("is_low_stock")]
            if low_items:
                items_str = ", ".join([f"**{p['product_name']}** ({p['quantity']} {p.get('unit','units')} bache hain)" for p in low_items[:4]])
                reply = f"Aapki dukaan mein **{len(low_items)} products** low stock par hain:\n{items_str}.\n\nInka reorder purchase order turant banayein taaki stock-out na ho."
            else:
                reply = "Bahut badiya! Filhal aapke sabhi mukhya products safe stock level par hain."
            return {"reply": reply, "grounded_sources": ["Inventory Stock Levels"]}

        # 4. Expiring products
        if any(w in msg_lower for w in ["expiry", "expire", "kharab", "date khatam"]):
            exp_rep = analytics_service.get_expiry_prevention_report(user_id)
            if exp_rep["items"]:
                items_str = "\n".join([f"• **{it['product_name']}** ({it['days_remaining']} din bache hain) — {it['recommendation']}" for it in exp_rep["items"][:3]])
                reply = f"Aapke **{exp_rep['expiring_batches_count']} batches** agle 30 dinon mein expire ho rahe hain (₹{exp_rep['total_at_risk_value']:,.2f} risk par):\n\n{items_str}"
            else:
                reply = "Aapke paas koi bhi product agle 30 dinon mein expire nahi hone wala hai."
            return {"reply": reply, "grounded_sources": ["Expiry Prevention Tracker"]}

        # 5. Dead stock / Slow moving
        if any(w in msg_lower for w in ["dead stock", "dead money", "slow", "fasa hua", "stuck capital"]):
            dead_rep = analytics_service.get_dead_money_report(user_id)
            if dead_rep["items"]:
                top = dead_rep["items"][0]
                reply = (
                    f"Aapka kul **₹{dead_rep['total_dead_money']:,.2f}** dead capital me fasa hua hai. "
                    f"Sabse slow product **{top['product_name']}** hai (pichhle {top['days_inactive']} dinon se koi sale nahi). "
                    f"\n\n**Recommendation**: {top['recommendation']}"
                )
            else:
                reply = "Aapka inventory turnover swasth hai. Koi bada dead capital nahi mila."
            return {"reply": reply, "grounded_sources": ["Dead Money Detector"]}

        # 6. Demand prediction explanation
        if any(w in msg_lower for w in ["demand prediction", "demand", "future sales", "forecast"]):
            pred_rep = prediction_service.get_demand_predictions(user_id)
            top = pred_rep.get("top_action_item")
            if top:
                reply = (
                    f"AI Demand Prediction aapki pichhli sales velocity aur weekly trends ko analyze karta hai. "
                    f"Udaharan ke liye, **{top['product_name']}** ki agle hafte ki expected demand **{top['expected_demand']} {top['unit']}s** hai "
                    f"aur stock-out se bachne ke liye **{top['recommended_order']} {top['unit']}s** order karne ki recommendation hai."
                )
            else:
                reply = "Demand prediction system sales trend aur season ke aadhar par bataata hai ki agle hafte kis product ki kitni bikri hogi taaki aap sahi quantity order kar sakein."
            return {"reply": reply, "grounded_sources": ["Prediction Intelligence"]}

        # 7. General help / Features
        reply = (
            "Main StockSathi Assistant hoon. Aap mujhse pooch sakte hain:\n\n"
            "• *'Aaj dukaan mein kya karna chahiye?'*\n"
            "• *'Mera total stock value kitna hai?'*\n"
            "• *'Kaunse products low stock hain?'*\n"
            "• *'Kitna dead money fasa hua hai?'*\n"
            "• *'Kaunsa maal expire hone wala hai?'*"
        )
        return {"reply": reply, "grounded_sources": ["StockSathi Knowledge Base"]}

support_service = SupportService()
