"""
Authentication API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any

from backend.services.auth_service import auth_service
from backend.security import get_current_user
from backend.services.subscription_service import subscription_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])

class SignupRequest(BaseModel):
    full_name: str
    shop_name: str
    phone: str
    email: str
    password: str
    confirm_password: str

class VerifyOtpRequest(BaseModel):
    identifier: str
    otp: str

class ResendOtpRequest(BaseModel):
    identifier: str

class LoginRequest(BaseModel):
    identifier: str
    password: str

class ForgotPasswordRequest(BaseModel):
    identifier: str

class ResetPasswordRequest(BaseModel):
    identifier: str
    otp: str
    new_password: str
    confirm_password: str

@router.post("/signup")
def signup(payload: SignupRequest):
    try:
        return auth_service.signup(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create account.")

@router.post("/verify-otp")
def verify_otp(payload: VerifyOtpRequest):
    try:
        return auth_service.verify_otp(payload.identifier, payload.otp)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/resend-otp")
def resend_otp(payload: ResendOtpRequest):
    try:
        return auth_service.resend_otp(payload.identifier)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login")
def login(payload: LoginRequest):
    try:
        return auth_service.login(payload.identifier, payload.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest):
    try:
        return auth_service.forgot_password_request(payload.identifier)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest):
    try:
        return auth_service.reset_password(
            payload.identifier, payload.otp, payload.new_password, payload.confirm_password
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/me")
def get_current_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    sub_status = subscription_service.get_user_subscription_status(user)
    return {
        "id": str(user["_id"]),
        "full_name": user["full_name"],
        "shop_name": user["shop_name"],
        "email": user["email"],
        "phone": user["phone"],
        "is_verified": user.get("is_verified", True),
        "language": user.get("language", "Hindi"),
        "settings": user.get("settings", {}),
        "subscription": sub_status,
        "is_demo_account": user.get("is_demo_account", False)
    }
