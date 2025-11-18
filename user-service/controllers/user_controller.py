from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime

from database import get_db
from models.user_model import User, UserRole
from services.user_service import UserService
from utils.jwt_handler import TokenManager, TokenData
from schemas.user_schemas import (
    UpdateUserProfileRequest,
    UserProfileResponse,
    UpdateUserRoleRequest,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    token_data: TokenData = Depends(TokenManager.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the current user's profile

    Args:
        token_data: JWT token data
        db: Database session

    Returns:
        User profile
    """
    return UserService.get_current_user_profile(int(token_data.sub), db)


@router.put("/me", response_model=UserProfileResponse)
async def update_current_user_profile(
    request: UpdateUserProfileRequest,
    token_data: TokenData = Depends(TokenManager.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the current user's profile

    Args:
        request: Profile update request
        token_data: JWT token data
        db: Database session

    Returns:
        Updated user profile
    """
    return UserService.update_user_profile(
        user_id=int(token_data.sub), update_data=request.dict(exclude_unset=True), db=db
    )


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    token_data: TokenData = Depends(TokenManager.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a user's profile by ID

    Args:
        user_id: User ID
        token_data: JWT token data
        db: Database session

    Returns:
        User profile

    Raises:
        HTTPException: If permission denied
    """
    # Only allow mentors or the user themselves to access profiles
    if token_data.role != UserRole.mentor.value and int(token_data.sub) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )

    return UserService.get_user_by_id(user_id, db)


@router.get("/", response_model=List[UserProfileResponse])
async def get_users(
    role: Optional[UserRole] = None,
    token_data: TokenData = Depends(TokenManager.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get users (restricted to mentors only)

    Args:
        role: Optional role filter
        token_data: JWT token data
        db: Database session

    Returns:
        List of user profiles

    Raises:
        HTTPException: If permission denied
    """
    # Only allow mentors to list users
    if (
        token_data.role != UserRole.mentor.value
        and token_data.role != UserRole.service.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )

    return UserService.get_users(role, db)


@router.post("/link-codeforces", response_model=UserProfileResponse)
async def link_codeforces_handle(
    codeforces_handle: str,
    token_data: TokenData = Depends(TokenManager.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Link a Codeforces handle to the user's account

    Args:
        codeforces_handle: Codeforces handle to link
        token_data: JWT token data
        db: Database session

    Returns:
        Updated user profile
    """
    return UserService.link_codeforces_handle(
        user_id=int(token_data.sub), codeforces_handle=codeforces_handle, db=db
    )


@router.put("/me/role", response_model=UserProfileResponse)
async def update_current_user_role(
    request: UpdateUserRoleRequest,
    token_data: TokenData = Depends(TokenManager.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the current user's role (learner or mentor)

    Args:
        request: Role update request
        token_data: JWT token data
        db: Database session

    Returns:
        Updated user profile

    Raises:
        HTTPException: If role is invalid
    """
    # Validate the role
    try:
        # Convert string to UserRole enum
        role = UserRole(request.role)
    except ValueError:
        valid_roles = [role.value for role in UserRole if role.value != "service"]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Valid roles are: {', '.join(valid_roles)}",
        )

    # Service role should not be settable by this endpoint
    if role == UserRole.service:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot set service role through this endpoint",
        )

    # Update only the role field
    return UserService.update_user_profile(
        user_id=int(token_data.sub), update_data={"role": role.value}, db=db
    )
