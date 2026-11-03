"""
Subscription and Feature-Gating Service
"""

import datetime
from typing import Dict, Any, Optional
from backend.config import config
from backend.database import get_db_collection

class Features:
    BASIC_INVENTORY = "BASIC_INVENTORY"
    DEMAND_PREDICTION = "DEMAND_PREDICTION"
    VOICE_AI = "VOICE_AI"
    SUPPLIER_COMPARISON = "SUPPLIER_COMPARISON"
    DEAD_MONEY = "DEAD_MONEY"
    EXPIRY_PREVENTION = "EXPIRY_PREVENTION"
    DAILY_ASSISTANT = "DAILY_ASSISTANT"
    AI_SUPPORT = "AI_SUPPORT"
    PURCHASE_ACTIONS = "PURCHASE_ACTIONS"
    ADVANCED_ANALYTICS = "ADVANCED_ANALYTICS"

PLANS = {
    "FREE": {
        "name": "Free Tier",
        "price": 0,
        "features": [Features.BASIC_INVENTORY],
        "description": "Essential stock records & basic product management"
    },
    "BASIC": {
        "name": "Basic",
        "price": 199,
        "period": "month",
        "features": [Features.BASIC_INVENTORY, Features.DAILY_ASSISTANT, Features.EXPIRY_PREVENTION],
        "description": "Daily actions & expiry loss prevention for small shops"
    },
    "STANDARD": {
        "name": "Standard",
        "price": 499,
        "period": "month",
        "features": [
            Features.BASIC_INVENTORY, Features.DAILY_ASSISTANT, Features.EXPIRY_PREVENTION,
            Features.DEAD_MONEY, Features.SUPPLIER_COMPARISON, Features.PURCHASE_ACTIONS
        ],
        "description": "Smart supplier comparison, dead money & purchase management"
    },
    "PREMIUM": {
        "name": "Premium",
        "price": 999,
        "period": "month",
        "features": [
            Features.BASIC_INVENTORY, Features.DEMAND_PREDICTION, Features.VOICE_AI,
            Features.SUPPLIER_COMPARISON, Features.DEAD_MONEY, Features.EXPIRY_PREVENTION,
            Features.DAILY_ASSISTANT, Features.AI_SUPPORT, Features.PURCHASE_ACTIONS,
            Features.ADVANCED_ANALYTICS
        ],
        "description": "Full AI Decision Engine, Voice AI, Demand Prediction & Shop Assistant"
    }
}

class SubscriptionService:
    
    @staticmethod
    def get_user_subscription_status(user: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates accurate subscription and trial status for a user."""
        plan = user.get("plan", "FREE")
        trial_started_at = user.get("trial_started_at")
        trial_ends_at = user.get("trial_ends_at")
        is_trial_active = False
        remaining_trial_days = 0
        remaining_trial_hours = 0
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        if trial_ends_at:
            try:
                if isinstance(trial_ends_at, str):
                    end_dt = datetime.datetime.fromisoformat(trial_ends_at.replace("Z", "+00:00"))
                else:
                    end_dt = trial_ends_at
                
                if end_dt > now:
                    is_trial_active = True
                    delta = end_dt - now
                    remaining_trial_days = max(0, delta.days)
                    remaining_trial_hours = int(delta.total_seconds() // 3600)
            except Exception:
                is_trial_active = False

        is_premium_active = (plan in ["PREMIUM", "STANDARD", "BASIC"]) or is_trial_active
        effective_plan = "TRIAL" if is_trial_active and plan == "FREE" else plan

        return {
            "plan": plan,
            "effective_plan": effective_plan,
            "is_trial_active": is_trial_active,
            "trial_started_at": trial_started_at,
            "trial_ends_at": trial_ends_at,
            "remaining_trial_days": remaining_trial_days,
            "remaining_trial_hours": remaining_trial_hours,
            "is_premium": is_premium_active,
            "unlocked_features": PLANS.get(plan, PLANS["FREE"])["features"] if not is_trial_active else PLANS["PREMIUM"]["features"]
        }

    @staticmethod
    def can_access_feature(user: Dict[str, Any], feature: str) -> bool:
        status = SubscriptionService.get_user_subscription_status(user)
        if feature == Features.BASIC_INVENTORY:
            return True
        return feature in status["unlocked_features"]

    @staticmethod
    def start_free_trial(user_id: str) -> Dict[str, Any]:
        users_coll = get_db_collection("users")
        user = users_coll.find_one({"_id": user_id})
        if not user:
            raise ValueError("User not found")
            
        if user.get("has_used_trial", False):
            raise ValueError("3-Day Free Trial has already been used for this shop account.")
            
        now = datetime.datetime.now(datetime.timezone.utc)
        trial_ends = now + datetime.timedelta(days=config.TRIAL_DURATION_DAYS)
        
        users_coll.update_one(
            {"_id": user_id},
            {"$set": {
                "trial_started_at": now.isoformat(),
                "trial_ends_at": trial_ends.isoformat(),
                "has_used_trial": True
            }}
        )
        
        # Log notification
        notifs_coll = get_db_collection("notifications")
        notifs_coll.insert_one({
            "user_id": user_id,
            "type": "TRIAL_ACTIVATED",
            "title": "🎉 3-Day Premium Trial Started",
            "message": f"All advanced AI decision, Voice AI and prediction features are unlocked until {trial_ends.strftime('%d %b %Y')}.",
            "is_read": False
        })
        
        updated_user = users_coll.find_one({"_id": user_id})
        return SubscriptionService.get_user_subscription_status(updated_user)

    @staticmethod
    def process_subscription_checkout(user_id: str, plan_name: str, payment_method: str, billing_cycle: str = "monthly") -> Dict[str, Any]:
        if plan_name not in ["BASIC", "STANDARD", "PREMIUM"]:
            raise ValueError("Invalid subscription plan selected.")
            
        users_coll = get_db_collection("users")
        subs_coll = get_db_collection("subscriptions")
        
        plan_info = PLANS[plan_name]
        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = now + datetime.timedelta(days=365 if billing_cycle == "yearly" else 30)
        
        sub_record = {
            "user_id": user_id,
            "plan": plan_name,
            "amount": plan_info["price"] * (10 if billing_cycle == "yearly" else 1),
            "currency": "INR",
            "payment_method": payment_method,
            "status": "ACTIVE",
            "billing_cycle": billing_cycle,
            "started_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "invoice_id": f"INV-SS-{now.strftime('%Y%m%d')}-{user_id[:6].upper()}"
        }
        
        subs_coll.insert_one(sub_record)
        
        users_coll.update_one(
            {"_id": user_id},
            {"$set": {
                "plan": plan_name,
                "subscription_id": sub_record["invoice_id"],
                "plan_expires_at": expires_at.isoformat()
            }}
        )
        
        notifs_coll = get_db_collection("notifications")
        notifs_coll.insert_one({
            "user_id": user_id,
            "type": "SUBSCRIPTION_ACTIVE",
            "title": f"✨ StockSathi {plan_name} Activated",
            "message": f"Thank you for upgrading! Your subscription is active until {expires_at.strftime('%d %b %Y')}.",
            "is_read": False
        })
        
        updated_user = users_coll.find_one({"_id": user_id})
        return {
            "subscription": sub_record,
            "user_status": SubscriptionService.get_user_subscription_status(updated_user)
        }

subscription_service = SubscriptionService()
