import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_

from db.database import SessionLocal
from models.contest import ContestModel
from schemas.contest_schema import ContestCreate, ContestNotificationMessage
from schemas.notification_schema import NotificationCreate

logger = logging.getLogger(__name__)


class ContestService:
    """Service for contest operations"""

    def create_or_update_contest(
        self, db: Session, contest_data: ContestCreate
    ) -> ContestModel:
        """Create a new contest or update if it already exists"""
        # Check if contest already exists
        existing_contest = (
            db.query(ContestModel)
            .filter(ContestModel.contest_id == contest_data.contest_id)
            .first()
        )

        if existing_contest:
            # Update existing contest
            for key, value in contest_data.dict().items():
                setattr(existing_contest, key, value)

            db.commit()
            db.refresh(existing_contest)
            logger.info(
                f"Updated contest {existing_contest.name} (ID: {existing_contest.contest_id})"
            )
            return existing_contest
        else:
            # Create new contest
            contest = ContestModel(**contest_data.dict())
            db.add(contest)
            db.commit()
            db.refresh(contest)
            logger.info(
                f"Created new contest {contest.name} (ID: {contest.contest_id})"
            )
            return contest

    def get_all_contests(
        self, db: Session, upcoming_only: bool = False
    ) -> List[ContestModel]:
        """Get all contests, optionally filtered for upcoming only"""
        query = db.query(ContestModel)

        if upcoming_only:
            # Filter for upcoming contests (phase = BEFORE)
            query = query.filter(ContestModel.phase == "BEFORE")

        return query.order_by(ContestModel.start_time).all()

    def get_contest_by_id(self, db: Session, contest_id: int) -> Optional[ContestModel]:
        """Get a contest by ID"""
        return (
            db.query(ContestModel).filter(ContestModel.contest_id == contest_id).first()
        )

    def mark_notification_sent(
        self, db: Session, contest_id: int
    ) -> Optional[ContestModel]:
        """Mark a contest as having had its notification sent"""
        contest = (
            db.query(ContestModel).filter(ContestModel.contest_id == contest_id).first()
        )

        if contest:
            contest.notification_sent = True
            db.commit()
            db.refresh(contest)
            logger.info(f"Marked notification as sent for contest {contest.name}")

        return contest

    def get_unsent_notifications(self, db: Session) -> List[ContestModel]:
        """Get contests that haven't had notifications sent yet"""
        return (
            db.query(ContestModel)
            .filter(
                ContestModel.notification_sent == False, ContestModel.phase == "BEFORE"
            )
            .order_by(ContestModel.start_time)
            .all()
        )

    def handle_contest_notification(self, message: Dict[str, Any]) -> None:
        """Process contest notification"""
        try:
            # Parse message with schema validation
            data_entry = message.get("data", {})

            logger.info(data_entry)

            contest_message = ContestNotificationMessage(**data_entry)
            logger.info(contest_message)
            # Convert timestamp to datetime if it's not already
            if isinstance(contest_message.start_time, (int, float)):
                start_time = datetime.fromtimestamp(contest_message.start_time)
            else:
                start_time = contest_message.start_time

            # Create contest data
            contest_data = ContestCreate(
                contest_id=contest_message.contest_id,
                name=contest_message.name,
                # type=contest_message.type,
                # phase="BEFORE",  # Assuming notifications are for upcoming contests
                start_time=start_time,
                duration_seconds=contest_message.duration_seconds,
                # description=contest_message.description,
                website_url=contest_message.website_url,
                notification_sent=False,
                # additional_data={},
            )

            # Save contest to database
            db = SessionLocal()
            try:
                self.create_or_update_contest(db, contest_data)
                logger.info(
                    f"Processed contest notification for contest {contest_message.name}"
                )

                # In a production system, you might also want to:
                # 1. Send a push notification to interested users
                # 2. Send an email notification
                # 3. Notify connected websocket clients
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling contest notification: {e}")
            raise
