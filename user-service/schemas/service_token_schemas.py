from pydantic import BaseModel


class ServiceTokenRequest(BaseModel):
    """Request model for service token authentication"""

    service_name: str
    service_secret: str


class TokenResponse(BaseModel):
    """Response model for authentication tokens"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 hours in seconds
