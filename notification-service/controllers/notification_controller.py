from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import SessionLocal
from services.notification_service import NotificationService
from schemas.notification_schema import NotificationResponse

router = APIRouter(tags=["Notification"])
service = NotificationService()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@router.get("/notification/user/{user_id}", response_model=List[NotificationResponse])
def get_user_notifications(user_id: str, db: Session = Depends(get_db)):
    """Get all notifications for a user"""
    notifications = service.get_user_notifications(db, user_id)
    return notifications


@router.put("/notification/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    """Mark a notification as read"""
    notification = service.mark_notification_read(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success"}


@router.put("/notification/user/{user_id}/read-all")
def mark_all_notifications_read(user_id: str, db: Session = Depends(get_db)):
    """Mark all notifications for a user as read"""
    service.mark_all_notifications_read(db, user_id)
    return {"status": "success"}
