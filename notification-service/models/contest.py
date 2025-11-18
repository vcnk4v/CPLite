from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from db.database import Base


class ContestModel(Base):
    __tablename__ = "contest"

    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    # type = Column(String(50), nullable=True)
    # phase = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    # description = Column(Text, nullable=True)
    website_url = Column(String(255), nullable=True)
    notification_sent = Column(Boolean, default=False)
    # additional_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
