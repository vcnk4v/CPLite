import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, Date, ForeignKey, JSON
from sqlalchemy.sql import func
from db.database import Base

# Define an enumeration for task status
class TaskStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    overdue = "overdue"

class Task(Base):
    __tablename__ = "assigned_tasks"

    id = Column(Integer, primary_key=True, index=True)
    userid = Column(Integer, nullable=False, index=True)
    mentorid = Column(Integer, nullable=False, index=True)
    due_date = Column(Date, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.pending, index=True)
    hasbeensubmittedbymentor = Column(Boolean, default=False)

    # Problem details
    # problem_id = Column(Integer, nullable=False) # contestId+index gives problem id and problem url
    problem_name = Column(String, default="Unknown")
    difficulty = Column(Integer, nullable=True)
    difficulty_category = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)
    matched_recommendation = Column(String, nullable=True)
    contestid = Column(String, default="Unknown") # multiple users can be tasked with same problem, so this isnt a key
    index = Column(String, default="") # multiple users can be tasked with same problem, so this isnt a key

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)