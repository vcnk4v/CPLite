import logging
from datetime import datetime
from typing import Dict, Any, List

from sqlalchemy.orm import Session

from db.database import SessionLocal
from models.notification import NotificationModel
from models.contest import ContestModel
from schemas.notification_schema import NotificationCreate, TaskCreatedMessage

logger = logging.getLogger(__name__)


class NotificationService:
    """Controller for notification operations"""

    def create_notification(
        self, db: Session, notification_data: NotificationCreate
    ) -> NotificationModel:
        """Create a new notification"""
        notification = NotificationModel(
            user_id=notification_data.user_id,
            content=notification_data.content,
            related_type=notification_data.related_type,
            related_id=notification_data.related_id,
            created_at=notification_data.created_at,
            is_read=notification_data.is_read,
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        logger.info(f"Created notification for user {notification_data.user_id}")
        return notification

    def get_user_notifications(
        self, db: Session, user_id: str
    ) -> List[NotificationModel]:
        """Get all notifications for a user"""
        return (
            db.query(NotificationModel)
            .filter(
                (NotificationModel.user_id == user_id)
                | (NotificationModel.user_id == "system")
            )
            .order_by(NotificationModel.created_at.desc())
            .all()
        )

    def mark_notification_read(
        self, db: Session, notification_id: int
    ) -> NotificationModel:
        """Mark a notification as read"""
        notification = (
            db.query(NotificationModel)
            .filter(NotificationModel.id == notification_id)
            .first()
        )

        if notification:
            notification.is_read = True
            db.commit()
            db.refresh(notification)

        return notification

    def mark_all_notifications_read(self, db: Session, user_id: str) -> int:
        """Mark all notifications for a user as read"""
        updated = (
            db.query(NotificationModel)
            .filter(
                NotificationModel.user_id == user_id, NotificationModel.is_read == False
            )
            .update({NotificationModel.is_read: True})
        )

        db.commit()
        return updated

    def handle_tasks_batch_created(self, message: Dict[str, Any]) -> None:
        """Process batch task created notifications"""
        try:
            tasks = message.get("tasks", [])

            # Group tasks by user_id for efficiency
            user_tasks = {}
            for task in tasks:
                user_id = task.get("user_id")
                if user_id not in user_tasks:
                    user_tasks[user_id] = []
                user_tasks[user_id].append(task)

            # Process notifications by user
            db = SessionLocal()
            try:
                for user_id, user_task_list in user_tasks.items():
                    # Handle individual task notifications
                    for task in user_task_list:
                        # Create notification content
                        notification_content = f"New task assigned: {task.get('title')}"
                        if task.get("due_date"):
                            notification_content += f" (due: {task.get('due_date')})"

                        # Create notification data
                        notification_data = NotificationCreate(
                            user_id=user_id,
                            content=notification_content,
                            related_type="task",
                            related_id=task.get("task_id"),
                            created_at=datetime.now(),
                            is_read=False,
                        )

                        self.create_notification(db, notification_data)

                    # Optional: Create a summary notification if multiple tasks
                    if len(user_task_list) > 1:
                        summary_content = (
                            f"{len(user_task_list)} new tasks have been assigned to you"
                        )
                        summary_notification = NotificationCreate(
                            user_id=user_id,
                            content=summary_content,
                            related_type="tasks_summary",
                            created_at=datetime.now(),
                            is_read=False,
                        )
                        self.create_notification(db, summary_notification)

                logger.info(f"Created batch notifications for {len(user_tasks)} users")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling tasks_batch_created notification: {e}")
            raise

    def handle_task_created(self, message: Dict[str, Any]) -> None:
        """Process task created notifications"""
        try:
            # Parse message with schema validation
            task_message = TaskCreatedMessage(**message)

            # Create notification content
            notification_content = f"New task assigned: {task_message.title}"
            if task_message.due_date:
                notification_content += f" (due: {task_message.due_date})"

            # Create notification data
            notification_data = NotificationCreate(
                user_id=task_message.user_id,
                content=notification_content,
                related_type="task",
                related_id=task_message.task_id,
                created_at=datetime.now(),
                is_read=False,
            )

            # Save notification to database
            db = SessionLocal()
            try:
                self.create_notification(db, notification_data)
                logger.info(
                    f"Created notification for user {task_message.user_id} about task {task_message.task_id}"
                )
                # In a production system, you might also want to:
                # 1. Send a push notification
                # 2. Send an email
                # 3. Notify connected websocket clients
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling task_created notification: {e}")
            raise

    def process_message(self, message: Dict[str, Any], message_type: str) -> None:
        """Route message to appropriate handler based on type"""
        if message_type == "task_created":
            self.handle_task_created(message)
        elif message_type == "contest_notification":
            self.handle_contest_notification(message)
        elif message_type == "tasks_batch_created":
            self.handle_tasks_batch_created(message)
        else:
            logger.warning(f"Unknown message type: {message_type}")

    def handle_contest_notification(self, message: Dict[str, Any]) -> None:
        """Process contest notifications"""
        try:
            from services.contest_service import ContestService

            # First, save the contest to the contest table and check if it was new
            contest_service = ContestService()

            # Parse message with schema validation
            data_entry = message.get("data", {})

            # Check if contest already exists in DB and notification was already sent
            db = SessionLocal()
            try:
                existing_contest = (
                    db.query(ContestModel)
                    .filter(ContestModel.contest_id == data_entry.get("id"))
                    .first()
                )

                # Only proceed with notification if:
                # 1. Contest doesn't exist in DB yet, OR
                # 2. Contest exists but notification_sent is False
                should_notify = not existing_contest

                # Always update/create the contest in DB
                contest_service.handle_contest_notification(message)

                if not should_notify:
                    logger.info(
                        f"Skipping notification for contest {data_entry.get('id')} - already notified"
                    )
                    return

                # If we get here, we should send a notification
                # Create a general notification for all users
                notification_content = (
                    f"Upcoming Codeforces contest: {data_entry['name']} "
                )

                # Format the start time
                if isinstance(data_entry["startTimeSeconds"], (int, float)):
                    start_time = datetime.fromtimestamp(data_entry["startTimeSeconds"])
                else:
                    start_time = data_entry["startTimeSeconds"]

                notification_content += (
                    f"starting at {start_time.strftime('%Y-%m-%d %H:%M:%S')}."
                )

                # Create notification data - using "system" as the user_id for global notifications
                notification_data = NotificationCreate(
                    user_id="system",
                    content=notification_content,
                    related_type="contest",
                    related_id=str(data_entry["id"]),
                    created_at=datetime.now(),
                    is_read=False,
                )

                # Save notification to database
                self.create_notification(db, notification_data)

                # Mark notification as sent for this contest
                contest_service.mark_notification_sent(db, data_entry["id"])

                logger.info(
                    f"Created contest notification for contest {data_entry['id']}"
                )
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling contest notification: {e}")
            raise
