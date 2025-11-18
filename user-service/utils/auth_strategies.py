from abc import ABC, abstractmethod
from typing import Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
import requests

import config
from models.user_model import User, AuthProvider, OAuthInfo, UserRole
from passlib.context import CryptContext


# Password context for handling password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthStrategy(ABC):
    """
    Abstract base class for authentication strategies
    """
    
    @abstractmethod
    async def authenticate(self, request_data: Dict[str, Any], db: Session) -> User:
        """
        Authenticate a user and return the user object
        
        Args:
            request_data: Authentication request data
            db: Database session
            
        Returns:
            Authenticated User object
        """
        pass
    
    @abstractmethod
    async def register(self, request_data: Dict[str, Any], db: Session) -> User:
        """
        Register a new user and return the user object
        
        Args:
            request_data: Registration request data
            db: Database session
            
        Returns:
            Newly registered User object
        """
        pass


class GoogleAuthStrategy(AuthStrategy):
    """
    Google OAuth authentication strategy
    """
    
    async def authenticate(self, request_data: Dict[str, Any], db: Session) -> User:
        """
        Authenticate with Google OAuth
        
        Args:
            request_data: Authentication request data, containing token or code
            db: Database session
            
        Returns:
            Authenticated User object
            
        Raises:
            HTTPException: If authentication fails
        """
        # We can now handle both token and code methods
        if "token" in request_data:
            # Direct token authentication (for API calls)
            token_info = await self._verify_google_token(request_data.get("token"))
        elif "code" in request_data:
            # OAuth code flow (from redirect)
            token_info = await self._exchange_code_for_token(request_data.get("code"))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either token or code is required",
            )
        
        if not token_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token or code",
            )
        
        # Get user info if not included in token_info
        if "email" not in token_info:
            token_info = await self._get_user_info(token_info.get("access_token"))
        
        # Check if user exists
        user = db.query(User).filter(
            User.email == token_info.get("email"),
            User.auth_provider == AuthProvider.google
        ).first()
        
        if not user:
            # Auto-register if user doesn't exist
            return await self.register(token_info, db)
        
        # Update OAuth info
        if user.oauth_info:
            user.oauth_info.access_token = token_info.get("access_token")
            user.oauth_info.refresh_token = token_info.get("refresh_token")
            user.oauth_info.expires_at = datetime.utcnow() + timedelta(seconds=token_info.get("expires_in", 3600))
        else:
            oauth_info = OAuthInfo(
                user_id=user.id,
                provider=AuthProvider.google,
                access_token=token_info.get("access_token"),
                refresh_token=token_info.get("refresh_token"),
                expires_at=datetime.utcnow() + timedelta(seconds=token_info.get("expires_in", 3600))
            )
            db.add(oauth_info)
        
        db.commit()
        return user
    
    async def register(self, request_data: Dict[str, Any], db: Session) -> User:
        """
        Register a new user with Google OAuth
        
        Args:
            request_data: Registration data from Google
            db: Database session
            
        Returns:
            Newly created User object
        """
        # Create new user from Google data
        new_user = User(
            name=request_data.get("name"),
            email=request_data.get("email"),
            role=UserRole.learner,  # Default role
            auth_provider=AuthProvider.google,
            provider_user_id=request_data.get("sub")  # Google's user ID
        )
        db.add(new_user)
        db.flush()  # To get the user ID
        
        # Add OAuth info
        oauth_info = OAuthInfo(
            user_id=new_user.id,
            provider=AuthProvider.google,
            access_token=request_data.get("access_token"),
            refresh_token=request_data.get("refresh_token"),
            expires_at=datetime.utcnow() + timedelta(seconds=request_data.get("expires_in", 3600))
        )
        db.add(oauth_info)
        
        db.commit()
        db.refresh(new_user)
        return new_user
    
    async def _verify_google_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Google ID token and return user info
        
        Args:
            token: Google ID token
            
        Returns:
            Dictionary with token info or None if verification fails
        """
        # Verify token with Google
        response = requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
        )
        
        if not response.ok:
            return None
        
        token_info = response.json()
        
        # Verify the token is for our app
        if token_info.get("aud") != config.GOOGLE_CLIENT_ID:
            return None
            
        return token_info
    
    async def _exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange OAuth code for tokens
        
        Args:
            code: OAuth authorization code
            
        Returns:
            Dictionary with token info or None if exchange fails
        """
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": config.GOOGLE_CLIENT_ID,
            "client_secret": config.GOOGLE_CLIENT_SECRET,
            "redirect_uri": config.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        response = requests.post(token_url, data=token_data)
        
        if not response.ok:
            return None
        
        token_info = response.json()
        
        # Get user info using the access token
        user_info = await self._get_user_info(token_info.get("access_token"))
        
        # Combine token info and user info
        return {**token_info, **user_info}
    
    async def _get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user info from Google using access token
        
        Args:
            access_token: Google OAuth access token
            
        Returns:
            Dictionary with user info
        """
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = requests.get(userinfo_url, headers=headers)
        
        if not response.ok:
            return {}
        
        return response.json()


class EmailAuthStrategy(AuthStrategy):
    """
    Email/password authentication strategy
    """
    
    async def authenticate(self, request_data: Dict[str, Any], db: Session) -> User:
        """
        Authenticate with email and password
        
        Args:
            request_data: Authentication data with email and password
            db: Database session
            
        Returns:
            Authenticated User object
            
        Raises:
            HTTPException: If authentication fails
        """
        email = request_data.get("email")
        password = request_data.get("password")
        
        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password required",
            )
        
        user = db.query(User).filter(
            User.email == email,
            User.auth_provider == AuthProvider.email
        ).first()
        
        if not user or not self._verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        return user
    
    async def register(self, request_data: Dict[str, Any], db: Session) -> User:
        """
        Register a new user with email and password
        
        Args:
            request_data: Registration data with email, password, and name
            db: Database session
            
        Returns:
            Newly created User object
            
        Raises:
            HTTPException: If registration fails
        """
        email = request_data.get("email")
        password = request_data.get("password")
        name = request_data.get("name")
        role = request_data.get("role", UserRole.learner)
        
        if not email or not password or not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email, password, and name required",
            )
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )
        
        # Create new user
        password_hash = self._get_password_hash(password)
        new_user = User(
            name=name,
            email=email,
            role=role,
            auth_provider=AuthProvider.email,
            password_hash=password_hash
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def _get_password_hash(self, password: str) -> str:
        """
        Generate a password hash
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)


class AuthStrategyFactory:
    """
    Factory for creating authentication strategy instances
    """
    
    @staticmethod
    def get_strategy(provider: AuthProvider) -> AuthStrategy:
        """
        Get the appropriate authentication strategy for a provider
        
        Args:
            provider: Authentication provider enum
            
        Returns:
            Authentication strategy instance
            
        Raises:
            ValueError: If provider is not supported
        """
        if provider == AuthProvider.google:
            return GoogleAuthStrategy()
        elif provider == AuthProvider.email:
            return EmailAuthStrategy()
        else:
            raise ValueError(f"Unsupported auth provider: {provider}")
