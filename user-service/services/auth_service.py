from datetime import timedelta
from typing import Dict, Any, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import config
from models.user_model import User, AuthProvider, UserRole
from utils.auth_strategies import AuthStrategyFactory
from utils.jwt_handler import TokenManager


class AuthService:
    """
    Service for authentication-related business logic
    """

    @staticmethod
    async def authenticate_with_google(
        token: str, db: Session
    ) -> Tuple[User, str, str]:
        """
        Authenticate a user with Google OAuth

        Args:
            token: Google OAuth token
            db: Database session

        Returns:
            Tuple containing (User, access_token, refresh_token)

        Raises:
            HTTPException: If authentication fails
        """
        try:
            strategy = AuthStrategyFactory.get_strategy(AuthProvider.google)
            user = await strategy.authenticate({"token": token}, db)

            # Create tokens
            access_token = TokenManager.create_access_token(
                data={"sub": str(user.id), "role": user.role.value},
                expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
            )
            refresh_token = TokenManager.create_refresh_token(
                data={"sub": str(user.id), "role": user.role.value}
            )

            return user, access_token, refresh_token

        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
            )

    @staticmethod
    async def register_with_email(
        email: str, password: str, name: str, role: UserRole, db: Session
    ) -> Tuple[User, str, str]:
        """
        Register a new user with email and password

        Args:
            email: User's email
            password: User's password
            name: User's name
            role: User's role
            db: Database session

        Returns:
            Tuple containing (User, access_token, refresh_token)

        Raises:
            HTTPException: If registration fails
        """
        try:
            strategy = AuthStrategyFactory.get_strategy(AuthProvider.email)
            user = await strategy.register(
                {"email": email, "password": password, "name": name, "role": role}, db
            )

            # Create tokens
            access_token = TokenManager.create_access_token(
                data={"sub": str(user.id), "role": user.role.value},
                expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
            )
            refresh_token = TokenManager.create_refresh_token(
                data={"sub": str(user.id), "role": user.role.value}
            )

            return user, access_token, refresh_token

        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {str(e)}",
            )

    @staticmethod
    async def login_with_email(
        email: str, password: str, db: Session
    ) -> Tuple[User, str, str]:
        """
        Login with email and password

        Args:
            email: User's email
            password: User's password
            db: Database session

        Returns:
            Tuple containing (User, access_token, refresh_token)

        Raises:
            HTTPException: If login fails
        """
        try:
            strategy = AuthStrategyFactory.get_strategy(AuthProvider.email)
            user = await strategy.authenticate(
                {"email": email, "password": password}, db
            )

            # Create tokens
            access_token = TokenManager.create_access_token(
                data={"sub": str(user.id), "role": user.role.value},
                expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
            )
            refresh_token = TokenManager.create_refresh_token(
                data={"sub": str(user.id), "role": user.role.value}
            )

            return user, access_token, refresh_token

        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Login failed: {str(e)}",
            )

    @staticmethod
    async def refresh_token(refresh_token: str, db: Session) -> Tuple[User, str, str]:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: Refresh token
            db: Database session

        Returns:
            Tuple containing (User, new_access_token, new_refresh_token)

        Raises:
            HTTPException: If token refresh fails
        """
        try:
            # Verify refresh token
            token_data = TokenManager.verify_token(refresh_token)

            # Get user from DB to ensure they still exist and are active
            user = db.query(User).filter(User.id == int(token_data.sub)).first()

            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive",
                )

            # Create new tokens
            access_token = TokenManager.create_access_token(
                data={"sub": str(user.id), "role": user.role.value},
                expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
            )
            new_refresh_token = TokenManager.create_refresh_token(
                data={"sub": str(user.id), "role": user.role.value}
            )

            return user, access_token, new_refresh_token

        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token refresh failed: {str(e)}",
            )
