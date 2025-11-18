from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
)
from sqlalchemy.sql import func
from db.database import Base


class NotificationModel(Base):
    __tablename__ = "notification"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    content = Column(Text, nullable=False)
    related_type = Column(String(50), nullable=True)
    related_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, nullable=False)
    is_read = Column(Boolean, default=False)
