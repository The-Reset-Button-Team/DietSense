"""
DietSense — Synchronization API Routes
Endpoints for manual sync trigger, status checking, and retry handling.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any
from app.core.dependencies import get_current_user
from app.core.sync_service import (
    get_sync_status,
    sync_user_data,
    retry_failed_sync,
)

router = APIRouter(prefix="/api/sync", tags=["Cloud Synchronization"])


@router.get("/status")
async def sync_status(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns the current synchronization status, queue depth, last synced timestamp,
    and cloud reachability for the authenticated user.
    """
    user_id = user["id"]
    return get_sync_status(user_id)


@router.post("/trigger")
async def trigger_sync(
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Triggers an immediate synchronization run for the authenticated user.
    Can be called manually from UI or automatically when connectivity returns.
    """
    user_id = user["id"]
    result = sync_user_data(user_id)
    return {
        "status": "success" if result["success"] else "partial",
        "result": result,
        "sync_info": get_sync_status(user_id),
    }


@router.post("/retry")
async def retry_sync(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Resets any failed queue mutations and re-attempts synchronization.
    """
    user_id = user["id"]
    result = retry_failed_sync(user_id)
    return {
        "status": "success" if result["success"] else "partial",
        "result": result,
        "sync_info": get_sync_status(user_id),
    }
