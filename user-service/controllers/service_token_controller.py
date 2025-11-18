from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
from typing import Optional
from datetime import timedelta

from database import get_db
from models.user_model import UserRole
from utils.jwt_handler import TokenManager

from schemas.service_token_schemas import (
    ServiceTokenRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["service-auth"])


@router.post("/service-token", response_model=TokenResponse)
async def create_service_token(
    request: ServiceTokenRequest, db: Session = Depends(get_db)
):
    """
    Create a service token for internal microservice authentication

    Args:
        request: Service token request

    Returns:
        Token response with access token
    """
    # Verify service credentials from environment variables or config
    # In production, you would use a more secure method
    expected_secret = os.getenv(
        f"{request.service_name.upper()}_SECRET", "your-service-secret"
    )

    if request.service_secret != expected_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service credentials",
        )

    # Create a service token with special permissions (role=service)
    access_token = TokenManager.create_service_token(
        service_name=request.service_name,
        permissions=["read:users", "write:tasks"],  # Special permissions for services
    )

    return TokenResponse(
        access_token=access_token,
    )
