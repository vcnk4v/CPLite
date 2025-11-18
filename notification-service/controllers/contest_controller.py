from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.database import SessionLocal
from services.contest_service import ContestService
from schemas.contest_schema import ContestResponse

router = APIRouter(tags=["Contests"])
service = ContestService()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/contests", response_model=List[ContestResponse])
def get_all_contests(
    upcoming_only: bool = Query(False, description="Show only upcoming contests"),
    db: Session = Depends(get_db),
):
    """Get all contests, optionally filtered for upcoming only"""
    contests = service.get_all_contests(db, upcoming_only=upcoming_only)
    return contests


@router.get("/contests/{contest_id}", response_model=ContestResponse)
def get_contest(contest_id: int, db: Session = Depends(get_db)):
    """Get a specific contest by ID"""
    contest = service.get_contest_by_id(db, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    return contest


@router.get("/contests/pending-notifications", response_model=List[ContestResponse])
def get_pending_notifications(db: Session = Depends(get_db)):
    """Get contests that haven't had notifications sent yet"""
    contests = service.get_unsent_notifications(db)
    return contests


@router.post("/contests/{contest_id}/mark-sent")
def mark_notification_sent(contest_id: int, db: Session = Depends(get_db)):
    """Mark a contest notification as sent"""
    contest = service.mark_notification_sent(db, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    return {"status": "success"}
