"""
Authentication Service
Handles user registration, phone/email OTP verification, login, and password recovery.
"""

import random
import datetime
from typing import Dict, Any, Optional
from backend.database import get_db_collection
from backend.config import config
from backend.security import hash_password, verify_password, validate_password_strength, create_access_token
from backend.services.subscription_service import subscription_service

class AuthService:

    DEFAULT_ADMIN_EMAIL = config.ADMIN_EMAIL

    @staticmethod
    def generate_otp() -> str:
        return f"{random.randint(100000, 999999)}"

    @staticmethod
    def ensure_default_admin() -> Optional[Dict[str, Any]]:
        users_coll = get_db_collection("users")
        admin = users_coll.find_one({"email": AuthService.DEFAULT_ADMIN_EMAIL})

        if admin:
            updates = {}
            if admin.get("role") != "admin":
                updates["role"] = "admin"
            if admin.get("is_admin") is not True:
                updates["is_admin"] = True
            if not admin.get("is_verified"):
                updates["is_verified"] = True
            if not admin.get("password_hash") and config.ADMIN_PASSWORD:
                updates["password_hash"] = hash_password(config.ADMIN_PASSWORD)
            if updates:
                users_coll.update_one({"_id": admin["_id"]}, {"$set": updates})
            return users_coll.find_one({"_id": admin["_id"]})

        if not config.ADMIN_PASSWORD:
            print("[AUTH] No admin account exists. Set ADMIN_PASSWORD to provision one.")
            return None

        admin_doc = {
            "full_name": "StockSathi Admin",
            "shop_name": "StockSathi Admin Console",
            "phone": "9999999999",
            "email": AuthService.DEFAULT_ADMIN_EMAIL,
            "password_hash": hash_password(config.ADMIN_PASSWORD),
            "role": "admin",
            "is_admin": True,
            "plan": "PREMIUM",
            "language": "Hindi",
            "is_verified": True,
            "has_used_trial": True,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "settings": {
                "low_stock_threshold": 10,
                "expiry_alert_days": 30,
                "language": "Hindi",
                "voice_speed": "normal",
                "notification_sms": True,
                "notification_whatsapp": True
            }
        }
        users_coll.insert_one(admin_doc)
        return admin_doc

    @staticmethod
    def signup(data: Dict[str, Any]) -> Dict[str, Any]:
        full_name = data.get("full_name", "").strip()
        shop_name = data.get("shop_name", "").strip()
        phone = data.get("phone", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        confirm_password = data.get("confirm_password", "")

        if not full_name or not shop_name or not phone or not email or not password:
            raise ValueError("All fields are required.")

        if password != confirm_password:
            raise ValueError("Passwords do not match.")

        pwd_validation = validate_password_strength(password)
        if not pwd_validation["is_valid"]:
            raise ValueError(" ".join(pwd_validation["errors"]))

        users_coll = get_db_collection("users")

        # Check existing user
        if users_coll.find_one({"email": email}):
            raise ValueError("An account with this email address already exists.")
        if users_coll.find_one({"phone": phone}):
            raise ValueError("An account with this phone number already exists.")

        otp_code = AuthService.generate_otp()
        now = datetime.datetime.now(datetime.timezone.utc)
        otp_expires = now + datetime.timedelta(minutes=15)

        user_doc = {
            "full_name": full_name,
            "shop_name": shop_name,
            "phone": phone,
            "email": email,
            "password_hash": hash_password(password),
            "plan": "FREE",
            "role": "user",
            "is_admin": False,
            "language": "Hindi",
            "is_verified": False,
            "verification_otp": otp_code,
            "otp_expires_at": otp_expires.isoformat(),
            "verification_channel": "email" if "@" in email else "phone",
            "has_used_trial": False,
            "created_at": now.isoformat(),
            "settings": {
                "low_stock_threshold": 10,
                "expiry_alert_days": 30,
                "language": "Hindi",
                "voice_speed": "normal",
                "notification_sms": True,
                "notification_whatsapp": True
            }
        }

        res = users_coll.insert_one(user_doc)
        user_id = str(res.inserted_id)

        return {
            "user_id": user_id,
            "email": email,
            "phone": phone,
            "is_verified": False,
            "message": "Account created. Please enter the verification OTP sent to your email/phone.",
            "dev_otp": otp_code  # For demo / testing convenience
        }

    @staticmethod
    def verify_otp(identifier: str, otp: str) -> Dict[str, Any]:
        """Verify phone or email using OTP."""
        users_coll = get_db_collection("users")
        clean_id = identifier.strip().lower()
        
        user = users_coll.find_one({
            "$or": [{"email": clean_id}, {"phone": clean_id}]
        })

        if not user:
            raise ValueError("Account not found with provided identifier.")

        if user.get("verification_otp") != otp.strip():
            raise ValueError("Invalid verification code. Please check and try again.")

        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at_str = user.get("otp_expires_at")
        if expires_at_str:
            expires_at = datetime.datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            if now > expires_at:
                raise ValueError("Verification code has expired. Please request a new OTP.")

        # Update verified status
        users_coll.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "is_verified": True,
                "verification_otp": None,
                "otp_expires_at": None
            }}
        )

        updated_user = users_coll.find_one({"_id": user["_id"]})
        token = create_access_token({"sub": str(updated_user["_id"])})
        sub_status = subscription_service.get_user_subscription_status(updated_user)

        user_payload = {
            "id": str(updated_user["_id"]),
            "full_name": updated_user["full_name"],
            "shop_name": updated_user["shop_name"],
            "email": updated_user["email"],
            "phone": updated_user["phone"],
            "role": updated_user.get("role", "user"),
            "is_admin": bool(updated_user.get("is_admin", False)),
            "is_verified": True,
            "language": updated_user.get("language", "Hindi"),
            "subscription": sub_status
        }

        return {
            "token": token,
            "user": user_payload,
            "message": "Account verified successfully!"
        }

    @staticmethod
    def resend_otp(identifier: str) -> Dict[str, Any]:
        users_coll = get_db_collection("users")
        clean_id = identifier.strip().lower()
        
        user = users_coll.find_one({
            "$or": [{"email": clean_id}, {"phone": clean_id}]
        })
        if not user:
            raise ValueError("Account not found.")

        otp_code = AuthService.generate_otp()
        now = datetime.datetime.now(datetime.timezone.utc)
        otp_expires = now + datetime.timedelta(minutes=15)

        users_coll.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "verification_otp": otp_code,
                "otp_expires_at": otp_expires.isoformat()
            }}
        )

        return {
            "message": "A new verification code has been generated.",
            "dev_otp": otp_code
        }

    @staticmethod
    def login(identifier: str, password: str) -> Dict[str, Any]:
        users_coll = get_db_collection("users")
        clean_id = identifier.strip().lower()

        user = users_coll.find_one({
            "$or": [{"email": clean_id}, {"phone": clean_id}]
        })

        auth_user = user

        if not auth_user or not verify_password(password, auth_user.get("password_hash", "")):
            raise ValueError("Invalid phone/email or password.")

        if not auth_user.get("is_verified", False):
            # Generate OTP for pending verification
            otp_code = AuthService.generate_otp()
            now = datetime.datetime.now(datetime.timezone.utc)
            users_coll.update_one(
                {"_id": auth_user["_id"]},
                {"$set": {
                    "verification_otp": otp_code,
                    "otp_expires_at": (now + datetime.timedelta(minutes=15)).isoformat()
                }}
            )
            return {
                "requires_verification": True,
                "identifier": auth_user["email"] or auth_user["phone"],
                "message": "Please verify your email/phone before accessing the dashboard.",
                "dev_otp": otp_code
            }

        token = create_access_token({"sub": str(auth_user["_id"])})
        sub_status = subscription_service.get_user_subscription_status(auth_user)

        user_payload = {
            "id": str(auth_user["_id"]),
            "full_name": auth_user["full_name"],
            "shop_name": auth_user["shop_name"],
            "email": auth_user["email"],
            "phone": auth_user["phone"],
            "role": auth_user.get("role", "user"),
            "is_admin": bool(auth_user.get("is_admin", False)),
            "is_verified": True,
            "language": auth_user.get("language", "Hindi"),
            "subscription": sub_status
        }

        return {
            "requires_verification": False,
            "token": token,
            "user": user_payload
        }

    @staticmethod
    def forgot_password_request(identifier: str) -> Dict[str, Any]:
        users_coll = get_db_collection("users")
        clean_id = identifier.strip().lower()

        user = users_coll.find_one({
            "$or": [{"email": clean_id}, {"phone": clean_id}]
        })
        if not user:
            raise ValueError("No account found with this phone number or email.")

        otp_code = AuthService.generate_otp()
        now = datetime.datetime.now(datetime.timezone.utc)
        users_coll.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "reset_otp": otp_code,
                "reset_otp_expires_at": (now + datetime.timedelta(minutes=15)).isoformat()
            }}
        )

        return {
            "message": "Password reset code sent to your phone/email.",
            "dev_otp": otp_code
        }

    @staticmethod
    def reset_password(identifier: str, otp: str, new_password: str, confirm_password: str) -> Dict[str, Any]:
        if new_password != confirm_password:
            raise ValueError("Passwords do not match.")

        pwd_val = validate_password_strength(new_password)
        if not pwd_val["is_valid"]:
            raise ValueError(" ".join(pwd_val["errors"]))

        users_coll = get_db_collection("users")
        clean_id = identifier.strip().lower()

        user = users_coll.find_one({
            "$or": [{"email": clean_id}, {"phone": clean_id}]
        })
        if not user:
            raise ValueError("Account not found.")

        if user.get("reset_otp") != otp.strip():
            raise ValueError("Invalid reset OTP code.")

        now = datetime.datetime.now(datetime.timezone.utc)
        expires_str = user.get("reset_otp_expires_at")
        if expires_str:
            expires_at = datetime.datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
            if now > expires_at:
                raise ValueError("Reset OTP has expired. Please request a new one.")

        users_coll.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "password_hash": hash_password(new_password),
                "reset_otp": None,
                "reset_otp_expires_at": None,
                "is_verified": True
            }}
        )

        return {"message": "Password has been reset successfully. You can now login."}

auth_service = AuthService()
