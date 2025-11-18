from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from typing import Union
from typing import List


class NotificationBase(BaseModel):
    """Base notification attributes"""

    user_id: Union[str, int]
    content: str
    related_type: Optional[str] = None
    related_id: Optional[Union[str, int]] = None
    is_read: bool = False


class NotificationCreate(NotificationBase):
    """Model for creating a notification"""

    created_at: datetime = Field(default_factory=datetime.now)


class NotificationResponse(NotificationBase):
    """Model for notification responses"""

    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class TaskCreatedMessage(BaseModel):
    """Schema for task created message"""

    task_id: Union[str, int]
    user_id: Union[str, int]
    title: str
    due_date: Optional[str] = None


class TaskMessage(BaseModel):
    """Schema for single task in a batch message"""

    task_id: Union[str, int]
    user_id: Union[str, int]
    title: str
    due_date: Optional[str] = None
    mentor_id: Optional[Union[str, int]] = None


class TasksBatchMessage(BaseModel):
    """Schema for batch task created message"""

    tasks: List[TaskMessage]
