from datetime import date, datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


# Mirror the TaskStatus enum for Pydantic
class TaskStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    overdue = "overdue"


class TaskCreate(BaseModel):
    userid: int
    mentorid: int
    due_date: Optional[date] = (
        None  # Now optional, will default to today+7 days if not provided
    )
    status: TaskStatus = TaskStatus.pending
    hasbeensubmittedbymentor: bool = False
    problem_name: str = "Unknown"
    difficulty: Optional[int] = None
    difficulty_category: Optional[str] = None
    tags: Optional[List[str]] = None
    matched_recommendation: Optional[str] = None
    contestid: str = "Unknown"
    index: str = ""


class TaskUpdate(BaseModel):
    # Make all fields optional for partial updates
    userid: Optional[int] = None
    mentorid: Optional[int] = None
    due_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    hasbeensubmittedbymentor: Optional[bool] = None
    problem_name: Optional[str] = None
    difficulty: Optional[int] = None
    difficulty_category: Optional[str] = None
    tags: Optional[List[str]] = None
    matched_recommendation: Optional[str] = None
    contestid: Optional[str] = None
    index: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    userid: int
    mentorid: int
    due_date: date
    status: str  # Will convert from enum
    hasbeensubmittedbymentor: bool
    problem_name: str
    difficulty: Optional[int]
    difficulty_category: Optional[str]
    tags: Optional[List[str]]
    matched_recommendation: Optional[str]
    contestid: str
    index: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskAssignRequest(BaseModel):
    """Request for assigning a task to a learner"""

    task_id: int
    due_date: date  # The due date to set when assigning the task
