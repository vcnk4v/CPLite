from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from database.connection import Base


class UserStats(Base):
    """
    Database model for user statistics.
    """
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True, index=True)
    codeforces_handle = Column(String, unique=True, index=True, nullable=False)
    summary = Column(String, nullable=True)
    stats = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UserStats(codeforces_handle='{self.codeforces_handle}')>"