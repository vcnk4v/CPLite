from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# Request models
class UpdateUserProfileRequest(BaseModel):
    """Request model for updating user profile"""

    name: Optional[str] = None
    codeforces_handle: Optional[str] = None
    url: Optional[str] = None


# Response models
class UserProfileResponse(BaseModel):
    """Response model for user profile"""

    id: int
    name: str
    email: str
    role: str
    codeforces_handle: Optional[str] = None
    url: Optional[str] = None
    date_created: datetime = None

    class Config:
        from_attributes = True


# Request model for role update
class UpdateUserRoleRequest(BaseModel):
    """Request model for updating user role"""

    role: str
