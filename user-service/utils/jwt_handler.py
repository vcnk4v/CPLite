from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel

import config


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class TokenData(BaseModel):
    """Token data model for JWT payload"""
    sub: str
    role: str
    exp: datetime
    permissions: Optional[List[str]] = None
    service_name: Optional[str] = None


class TokenManager:
    """
    Token management utilities for creating and verifying JWT tokens
    """
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a new JWT access token
        
        Args:
            data: Dictionary containing data to encode in the token
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
            
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """
        Create a new JWT refresh token with a longer expiration
        
        Args:
            data: Dictionary containing data to encode in the token
            
        Returns:
            Encoded JWT refresh token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
        
        return encoded_jwt
    
    @staticmethod
    def create_service_token(service_name: str, permissions: List[str]) -> str:
        """
        Create a new JWT token for service-to-service communication
        
        Args:
            service_name: Name of the service
            permissions: List of permissions for the service
            
        Returns:
            Encoded JWT service token string
        """
        # Service tokens have longer expiration (24 hours)
        expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode = {
            "sub": "service",
            "role": "service",
            "service_name": service_name,
            "permissions": permissions,
            "exp": expire
        }
        
        encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
        
        return encoded_jwt
    
    # @staticmethod
    # def verify_token(token: str) -> TokenData:
    #     """
    #     Verify a JWT token and return the payload
        
    #     Args:
    #         token: JWT token string to verify
            
    #     Returns:
    #         TokenData containing user ID, role, and expiration
            
    #     Raises:
    #         HTTPException: If token is invalid or expired
    #     """
    #     try:
    #         payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
            
    #         # Extract required fields
    #         user_id = payload.get("sub")
    #         role = payload.get("role")
    #         exp = datetime.fromtimestamp(payload.get("exp"))
    #         permissions = payload.get("permissions")
    #         service_name = payload.get("service_name")
            
    #         if user_id is None or role is None:
    #             raise HTTPException(
    #                 status_code=status.HTTP_401_UNAUTHORIZED,
    #                 detail="Invalid token payload",
    #                 headers={"WWW-Authenticate": "Bearer"},
    #             )
                
    #         return TokenData(
    #             sub=user_id, 
    #             role=role, 
    #             exp=exp, 
    #             permissions=permissions,
    #             service_name=service_name
    #         )
            
    #     except JWTError:
    #         raise HTTPException(
    #             status_code=status.HTTP_401_UNAUTHORIZED,
    #             detail="Could not validate credentials",
    #             headers={"WWW-Authenticate": "Bearer"},
    #         )
    
    @staticmethod
    def verify_token(token: str) -> TokenData:
        """
        Verify a JWT token and return the payload
        
        Args:
            token: JWT token string to verify
            
        Returns:
            TokenData containing user ID, role, and expiration
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Print token details for debugging
            print(f"Verifying token: {token}")
            
            # Decode the token
            payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
            
            # Print payload for debugging
            print(f"Token payload: {payload}")
            
            # Extract required fields
            user_id = payload.get("sub")
            role = payload.get("role")
            exp = datetime.fromtimestamp(payload.get("exp"))
            permissions = payload.get("permissions")
            service_name = payload.get("service_name")
            
            if user_id is None or role is None:
                print(f"Invalid token payload: missing user_id or role")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            return TokenData(
                sub=user_id, 
                role=role, 
                exp=exp, 
                permissions=permissions,
                service_name=service_name
            )
            
        except JWTError as e:
            print(f"JWT Error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
        """
        Get current user from JWT token (to be used as a FastAPI dependency)
        
        Args:
            token: JWT token from Authorization header
            
        Returns:
            TokenData containing user information
        """
        return TokenManager.verify_token(token)
    
    @staticmethod
    async def verify_service_token(token: str = Depends(oauth2_scheme)) -> TokenData:
        """
        Verify that a token is a valid service token with appropriate permissions
        
        Args:
            token: JWT token from Authorization header
            
        Returns:
            TokenData containing service information
            
        Raises:
            HTTPException: If token is not a valid service token
        """
        token_data = TokenManager.verify_token(token)
        
        if token_data.role != "service" or not token_data.service_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This endpoint requires a service token",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return token_data
    
    @staticmethod
    async def has_permission(permission: str, token_data: TokenData = Depends(get_current_user)) -> bool:
        """
        Check if the token has a specific permission
        
        Args:
            permission: Permission to check for
            token_data: Token data from get_current_user
            
        Returns:
            True if token has the permission, False otherwise
        """
        # Service tokens have explicit permissions
        if token_data.role == "service" and token_data.permissions:
            return permission in token_data.permissions
        
        # Regular user tokens have role-based implicit permissions
        # For simplicity, mentors have all permissions
        if token_data.role == "mentor":
            return True
            
        # Add more role-based permission logic here
        
        return False
