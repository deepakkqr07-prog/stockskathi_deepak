"""Administrator-only dashboard endpoints."""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from backend.database import get_db_collection
from backend.security import require_admin

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/overview")
def get_admin_overview(_: Dict[str, Any] = Depends(require_admin)):
    users = get_db_collection("users")
    total_users = users.count_documents({})
    verified_users = users.count_documents({"is_verified": True})
    admins = users.count_documents({"$or": [{"role": "admin"}, {"is_admin": True}]})
    recent_users = users.find(
        {},
        {
            "full_name": 1,
            "shop_name": 1,
            "email": 1,
            "role": 1,
            "is_verified": 1,
            "created_at": 1,
        },
        sort=[("created_at", -1)],
        limit=10,
    )

    return {
        "summary": {
            "total_users": total_users,
            "verified_users": verified_users,
            "pending_verification": total_users - verified_users,
            "admin_users": admins,
        },
        "recent_users": [
            {
                "id": str(user.get("_id", "")),
                "full_name": user.get("full_name", ""),
                "shop_name": user.get("shop_name", ""),
                "email": user.get("email", ""),
                "role": "admin" if user.get("role") == "admin" or user.get("is_admin") is True else "user",
                "is_verified": bool(user.get("is_verified", False)),
                "created_at": user.get("created_at"),
            }
            for user in recent_users
        ],
    }
