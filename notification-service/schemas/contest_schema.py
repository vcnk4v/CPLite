from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, Union


class ContestBase(BaseModel):
    """Base contest attributes"""

    contest_id: int
    name: str
    # type: Optional[str] = None
    # phase: str
    start_time: datetime
    duration_seconds: int
    # description: Optional[str] = None
    website_url: Optional[str] = None
    notification_sent: bool = False
    # additional_data: Optional[Dict[str, Any]] = None


class ContestCreate(ContestBase):
    """Model for creating a contest"""

    pass


class ContestResponse(ContestBase):
    """Model for contest responses"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ContestNotificationMessage(BaseModel):
    """Schema for contest notification message"""

    contest_id: int = Field(alias="id")  # Map 'id' from input to 'contest_id'
    name: str
    # type: Optional[str] = None
    start_time: datetime = Field(
        alias="startTimeSeconds", default_factory=lambda: datetime.now()
    )
    duration_seconds: int = Field(alias="durationSeconds")
    website_url: Optional[str] = None

    class Config:
        populate_by_name = True
        populate_by_alias = True
