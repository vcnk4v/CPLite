from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime


class UserProgressStat(BaseModel):
    """Schema for user progress stats."""

    date: str
    problems_solved: int


class UserStatsData(BaseModel):
    """Schema for user stats data."""

    total_solved: int
    progress_over_time: List[UserProgressStat]
    difficulty_distribution: Dict[str, int]
    tag_distribution: Dict[str, int]


class UserInfoSchema(BaseModel):
    """Schema for user info."""

    rating: Optional[int] = None
    max_rating: Optional[int] = None
    rank: Optional[str] = None
    contribution: Optional[int] = None
    friend_of_count: Optional[int] = None
    registration_time: Optional[int] = None
    last_online_time: Optional[int] = None


class UserStatsResponse(BaseModel):
    """Schema for user stats response."""

    handle: str
    user_info: UserInfoSchema
    problems_count: int
    summary: str
    stats: UserStatsData


class WeeklySummaryResponse(BaseModel):
    """Schema for weekly summary response."""

    handle: str
    summary: str


class WeeklyStatsResponse(BaseModel):
    """Schema for weekly stats response."""

    handle: str
    user_info: UserInfoSchema
    stats: UserStatsData


class UserStatsDB(BaseModel):
    """Schema for database model representation."""

    id: int
    codeforces_handle: str
    summary: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
