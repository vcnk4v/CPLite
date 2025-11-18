from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel

from database import get_db
from models.user_model import UserRole
from services.auth_service import AuthService
from utils.jwt_handler import TokenManager


router = APIRouter(prefix="/auth", tags=["authentication"])


# Request models
class GoogleAuthRequest(BaseModel):
    """Request model for Google authentication"""

    token: str
    role: Optional[UserRole] = UserRole.learner


class EmailRegisterRequest(BaseModel):
    """Request model for email registration"""

    email: str
    password: str
    name: str
    role: Optional[UserRole] = UserRole.learner


class EmailLoginRequest(BaseModel):
    """Request model for email login"""

    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh"""

    refresh_token: str


# Response models
class TokenResponse(BaseModel):
    """Response model for authentication tokens"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds
    user_id: int
    role: str


@router.post("/google", response_model=TokenResponse)
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Authenticate with Google OAuth

    Args:
        request: Google authentication request
        db: Database session

    Returns:
        Token response with access and refresh tokens
    """
    user, access_token, refresh_token = await AuthService.authenticate_with_google(
        token=request.token, db=db
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        role=user.role.value,
    )


@router.post("/register", response_model=TokenResponse)
async def register(request: EmailRegisterRequest, db: Session = Depends(get_db)):
    """
    Register with email and password

    Args:
        request: Email registration request
        db: Database session

    Returns:
        Token response with access and refresh tokens
    """
    user, access_token, refresh_token = await AuthService.register_with_email(
        email=request.email,
        password=request.password,
        name=request.name,
        role=request.role,
        db=db,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        role=user.role.value,
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: EmailLoginRequest, db: Session = Depends(get_db)):
    """
    Login with email and password

    Args:
        request: Email login request
        db: Database session

    Returns:
        Token response with access and refresh tokens
    """
    user, access_token, refresh_token = await AuthService.login_with_email(
        email=request.email, password=request.password, db=db
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        role=user.role.value,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token

    Args:
        request: Refresh token request
        db: Database session

    Returns:
        Token response with new access and refresh tokens
    """
    user, access_token, refresh_token = await AuthService.refresh_token(
        refresh_token=request.refresh_token, db=db
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        role=user.role.value,
    )
