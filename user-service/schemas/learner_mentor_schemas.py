from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from models.user_model import UserRole


# Request models
class AssignMentorRequest(BaseModel):
    """Request model to assign a mentor to a learner"""

    learner_id: int
    mentor_id: int


class UpdateMentorRelationshipRequest(BaseModel):
    """Request model to update a mentor-learner relationship"""

    is_active: bool


# Response models
class MentorLearnerResponse(BaseModel):
    """Response model for mentor-learner relationship details"""

    id: int
    mentor_id: int
    learner_id: int
    date_created: datetime
    is_active: bool

    class Config:
        from_attributes = True


class AssignMentorResponse(BaseModel):
    """Response model for mentor assignment"""

    mentor_id: int
    learner_id: int
    success: bool
    message: str


# User schema for response
class UserSchema(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole

    class Config:
        from_attributes = True


class MentorLearnerListResponse(BaseModel):
    """Response model for listing all mentors and learners"""

    mentors: List[UserSchema]
    learners: List[UserSchema]
    success: bool
    message: str


class LearnerMentorResponse(BaseModel):
    """Response model for listing mentors of a specific learner"""

    learner_id: int
    mentor_id: int
    mentor: Optional[UserSchema] = None
    success: bool
    message: str


class MentorResponse(BaseModel):
    """Response model for mentor details"""

    id: int
    name: str
    codeforces_handle: Optional[str] = None
    url: Optional[str] = None
    email: str

    class Config:
        from_attributes = True

class LearnerResponse(BaseModel):
    id: int
    name: str
    email: str
    codeforces_handle: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class MentorLearnersResponse(BaseModel):
    success: bool
    message: str
    learners: List[LearnerResponse]