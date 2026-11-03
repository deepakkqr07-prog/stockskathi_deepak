"""
Voice AI Service: Real-Time Natural Language Inventory Command Parser & Confirmation Engine
Supports Hindi, Punjabi, English, and Hinglish.
Follows the strict protocol:
SPEAK -> UNDERSTAND -> READ BACK (+DIFF) -> CONFIRM/CORRECT -> UPDATE -> VOICE SUCCESS
"""

import re
import datetime
from typing import Dict, Any, Optional, Tuple
from backend.database import get_db_collection
from backend.services.inventory_service import inventory_service

HINDI_NUMBER_MAP = {
    "ek": 1, "do": 2, "teen": 3, "char": 4, "chaar": 4, "paanch": 5, "panch": 5, "che": 6, "chhe": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
    "gyarah": 11, "barah": 12, "terah": 13, "chaudah": 14, "pandrah": 15, "solah": 16, "satrah": 17, "atharah": 18, "unnis": 19, "bees": 20,
    "pachees": 25, "tees": 30, "pentees": 35, "chalis": 40, "pachas": 50, "saath": 60, "sattar": 70, "assi": 80, "nabbe": 90, "sau": 100,
    "ik": 1, "trai": 3, "panj": 5, "chhe": 6, "satt": 7, "atth": 8, "nau": 9, "dass": 10, "vi": 20, "tee": 30
}

class VoiceService:

    @staticmethod
    def extract_number(text: str) -> Optional[int]:
        # Search for digit
        digit_match = re.search(r"\b(\d+)\b", text)
        if digit_match:
            return int(digit_match.group(1))
            
        words = text.lower().split()
        for w in words:
            clean_w = re.sub(r"[^\w]", "", w)
            if clean_w in HINDI_NUMBER_MAP:
                return HINDI_NUMBER_MAP[clean_w]
        return None

    @staticmethod
    def extract_product_match(user_id: str, text: str) -> Optional[Dict[str, Any]]:
        products = inventory_service.get_products(user_id)
        lower_text = text.lower()
        
        # Exact product name check
        for p in products:
            p_name = p.get("product_name", "").lower()
            if p_name in lower_text:
                return p
                
        # Word token overlap check
        words = set(re.findall(r"\b\w+\b", lower_text))
        for p in products:
            p_words = set(re.findall(r"\b\w+\b", p.get("product_name", "").lower()))
            if p_words and (p_words.issubset(words) or any(pw in words for pw in p_words if len(pw) > 3)):
                return p
                
        return None

    @staticmethod
    def parse_command(user_id: str, transcript: str, language: str = "Hindi", existing_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parses spoken command, determines intent, finds matching product, and prepares readback.
        """
        clean_text = transcript.strip()
        lower_text = clean_text.lower()
        
        # Check confirmation intent if existing pending action exists
        is_confirmation = bool(re.search(r"\b(haan|ha|yes|yep|sure|kar do|kardo|update karo|theek hai|proceed|okay|ok)\b", lower_text))
        is_cancellation = bool(re.search(r"\b(cancel|radd|nahi karna|mat karo|chhod do|stop|no)\b", lower_text))
        is_correction = bool(re.search(r"\b(nahi|no|change karo|galat hai|nahin|badlo)\b", lower_text))

        if existing_context and is_confirmation and not is_correction:
            return {
                "intent": "CONFIRM_ACTION",
                "status": "READY_TO_EXECUTE",
                "pending_action": existing_context,
                "message": "Executing confirmed action..."
            }

        # Determine target product
        product = VoiceService.extract_product_match(user_id, lower_text)
        if not product and existing_context and "product_id" in existing_context:
            # Carry over product from prior turn if correcting quantity
            product = inventory_service.get_product(user_id, existing_context["product_id"])

        if not product:
            return {
                "intent": "UNKNOWN",
                "status": "PRODUCT_NOT_FOUND",
                "transcript": clean_text,
                "readback_text": "Kripya product ka naam spasht karein (jaise 'Maggi mein 20 packet add karo').",
                "speech_response": "Kripya product ka naam spasht karein.",
                "pending_action": None
            }

        qty = VoiceService.extract_number(lower_text)
        if qty is None:
            if existing_context and "proposed_quantity" in existing_context:
                qty = existing_context["proposed_quantity"]
            else:
                return {
                    "intent": "INCOMPLETE_QTY",
                    "status": "QTY_REQUIRED",
                    "product": product,
                    "readback_text": f"{product['product_name']} ke liye kitni quantity update karni hai?",
                    "speech_response": f"{product['product_name']} ke liye kitni quantity update karni hai?",
                    "pending_action": None
                }

        # Determine Action Type: ADD / SUBTRACT / SET_EXACT
        current_stock = product.get("quantity", 0)
        unit = product.get("unit", "packet")
        p_name = product.get("product_name")

        if any(w in lower_text for w in ["add", "jodo", "aur", "badhao", "increase", "extra", "plus", "paao"]):
            action_type = "ADD"
            delta = qty
            new_stock = current_stock + delta
            diff_label = f"+{delta} {unit}"
        elif any(w in lower_text for w in ["becha", "kam", "ghatao", "minus", "remove", "sold", "sub", "nikalo"]):
            action_type = "SUBTRACT"
            delta = -qty
            new_stock = max(0, current_stock - qty)
            diff_label = f"-{qty} {unit}"
        elif any(w in lower_text for w in ["set", "kardo", "kar do", "bana do", "fix"]):
            action_type = "SET_EXACT"
            delta = qty - current_stock
            new_stock = qty
            diff_label = f"Set to {qty} {unit}"
        else:
            # Default to Add if "aur" / "packet" mentioned
            action_type = "ADD"
            delta = qty
            new_stock = current_stock + delta
            diff_label = f"+{delta} {unit}"

        # Generate culturally natural, professional Hindi / Hinglish readback
        if language in ["Hindi", "Hinglish"]:
            readback_spoken = (
                f"Main {p_name} ke stock mein {qty} {unit}s add karne wala hoon. "
                f"Current stock {current_stock} hai aur update ke baad {new_stock} ho jayega. "
                f"Kya main update kar doon?"
            ) if action_type == "ADD" else (
                f"Main {p_name} ke stock se {qty} {unit}s kam karne wala hoon. "
                f"Current stock {current_stock} se ghatkar {new_stock} ho jayega. "
                f"Kya main update kar doon?"
            )
        elif language == "Punjabi":
            readback_spoken = (
                f"Main {p_name} de stock vich {qty} {unit} add karan laga haan. "
                f"Pehla stock {current_stock} si te update toh baad {new_stock} ho javega. "
                f"Ki main update kar devan?"
            )
        else:
            readback_spoken = (
                f"I am ready to add {qty} {unit}s to {p_name}. "
                f"Current stock is {current_stock} and new stock will be {new_stock}. "
                f"Should I proceed with the update?"
            )

        pending_action = {
            "product_id": str(product["_id"]),
            "product_name": p_name,
            "unit": unit,
            "action_type": action_type,
            "delta": delta,
            "current_stock": current_stock,
            "new_stock": new_stock,
            "proposed_quantity": qty,
            "diff_label": diff_label,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        return {
            "intent": "STOCK_UPDATE_PROPOSED",
            "status": "CONFIRMATION_REQUIRED",
            "transcript": clean_text,
            "readback_text": readback_spoken,
            "speech_response": readback_spoken,
            "pending_action": pending_action,
            "display": {
                "product_name": p_name,
                "current_stock": current_stock,
                "change": f"+{delta}" if delta >= 0 else f"{delta}",
                "new_stock": new_stock,
                "unit": unit
            }
        }

    @staticmethod
    def execute_confirmed_action(user_id: str, pending_action: Dict[str, Any], language: str = "Hindi") -> Dict[str, Any]:
        """
        Executes database update ONLY after user confirms with 'Haan' / 'Confirm'.
        Generates spoken confirmation feedback.
        """
        product_id = pending_action.get("product_id")
        delta = pending_action.get("delta")
        new_stock = pending_action.get("new_stock")
        p_name = pending_action.get("product_name", "Product")
        unit = pending_action.get("unit", "packet")

        # Perform actual database update
        result = inventory_service.adjust_stock(
            user_id=user_id,
            product_name_or_id=product_id,
            exact_qty=new_stock,
            reason="Voice AI Assistant Command"
        )

        prev_qty = result["previous_quantity"]
        updated_qty = result["new_quantity"]
        added_qty = updated_qty - prev_qty

        # Generate natural spoken success response
        if language in ["Hindi", "Hinglish"]:
            speech_success = f"Ho gaya ji! {p_name} ka stock successfully update kar diya gaya hai. Ab total stock {updated_qty} {unit}s hai."
        elif language == "Punjabi":
            speech_success = f"Ho gaya ji! {p_name} da stock update ho gaya hai. Hun kul stock {updated_qty} {unit}s hai."
        else:
            speech_success = f"Done! Successfully updated {p_name} inventory. Current stock is now {updated_qty} {unit}s."

        # Notification
        notifs = get_db_collection("notifications")
        notifs.insert_one({
            "user_id": user_id,
            "type": "VOICE_STOCK_UPDATE",
            "title": f"🎤 Voice Update: {p_name}",
            "message": f"Stock changed from {prev_qty} to {updated_qty} {unit}s via Voice Assistant.",
            "is_read": False
        })

        return {
            "success": True,
            "message": f"✓ Stock Updated: {p_name}",
            "speech_response": speech_success,
            "details": {
                "product_name": p_name,
                "previous_stock": prev_qty,
                "added": added_qty,
                "new_stock": updated_qty,
                "unit": unit
            }
        }

voice_service = VoiceService()
