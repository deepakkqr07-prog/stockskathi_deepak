"""
Authentication Service
Handles user registration, phone/email OTP verification, login, and password recovery.
"""

import random
import datetime
from typing import Dict, Any, Optional
from backend.database import get_db_collection
from backend.security import hash_password, verify_password, validate_password_strength, create_access_token
from backend.services.subscription_service import subscription_service

class AuthService:

    @staticmethod
    def generate_otp() -> str:
        return f"{random.randint(100000, 999999)}"

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

        return {
            "token": token,
            "user": {
                "id": str(updated_user["_id"]),
                "full_name": updated_user["full_name"],
                "shop_name": updated_user["shop_name"],
                "email": updated_user["email"],
                "phone": updated_user["phone"],
                "is_verified": True,
                "language": updated_user.get("language", "Hindi"),
                "subscription": sub_status
            },
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

        if not user or not verify_password(password, user.get("password_hash", "")):
            raise ValueError("Invalid phone/email or password.")

        if not user.get("is_verified", False):
            # Generate OTP for pending verification
            otp_code = AuthService.generate_otp()
            now = datetime.datetime.now(datetime.timezone.utc)
            users_coll.update_one(
                {"_id": user["_id"]},
                {"$set": {
                    "verification_otp": otp_code,
                    "otp_expires_at": (now + datetime.timedelta(minutes=15)).isoformat()
                }}
            )
            return {
                "requires_verification": True,
                "identifier": user["email"] or user["phone"],
                "message": "Please verify your email/phone before accessing the dashboard.",
                "dev_otp": otp_code
            }

        token = create_access_token({"sub": str(user["_id"])})
        sub_status = subscription_service.get_user_subscription_status(user)

        return {
            "requires_verification": False,
            "token": token,
            "user": {
                "id": str(user["_id"]),
                "full_name": user["full_name"],
                "shop_name": user["shop_name"],
                "email": user["email"],
                "phone": user["phone"],
                "is_verified": True,
                "language": user.get("language", "Hindi"),
                "subscription": sub_status
            }
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
