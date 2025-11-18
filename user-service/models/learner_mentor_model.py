from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class MentorLearnerRelationship(Base):
    """Association table connecting mentors with learners"""
    __tablename__ = "mentor_learner_relationships"

    id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    learner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date_created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Define relationships to User model for both roles
    mentor = relationship("User", foreign_keys=[mentor_id])
    learner = relationship("User", foreign_keys=[learner_id])