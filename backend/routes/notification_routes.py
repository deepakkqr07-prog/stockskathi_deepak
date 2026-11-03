"""
Notifications API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from backend.database import get_db_collection
from backend.security import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("/")
def get_notifications(user: Dict[str, Any] = Depends(get_current_user)):
    notifs_coll = get_db_collection("notifications")
    notifs = notifs_coll.find({"user_id": str(user["_id"])}, sort=[("created_at", -1)], limit=20)
    unread_count = sum(1 for n in notifs if not n.get("is_read", False))
    return {
        "unread_count": unread_count,
        "notifications": notifs
    }

@router.patch("/{notification_id}/read")
def mark_read(notification_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    notifs_coll = get_db_collection("notifications")
    notifs_coll.update_one(
        {"_id": notification_id, "user_id": str(user["_id"])},
        {"$set": {"is_read": True}}
    )
    return {"success": True}

@router.post("/mark-all-read")
def mark_all_read(user: Dict[str, Any] = Depends(get_current_user)):
    notifs_coll = get_db_collection("notifications")
    notifs_coll.update_many(
        {"user_id": str(user["_id"])},
        {"$set": {"is_read": True}}
    )
    return {"success": True}
