from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime
import os
from typing import List, Optional

# JWT configuration - should be the same across all microservices
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")  # In production, use a secure environment variable
ALGORITHM = "HS256"

# Security scheme for getting the token from the Authorization header
security = HTTPBearer()

class AuthMiddleware:
    """
    Middleware for handling authentication between microservices.
    This class can be used in any microservice that needs to validate JWT tokens.
    """
    
    @staticmethod
    async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """
        Verify the JWT token from the Authorization header
        """
        token = credentials.credentials
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Extract required fields
            user_id = payload.get("sub")
            role = payload.get("role")
            exp = payload.get("exp")
            permissions = payload.get("permissions", [])
            service_name = payload.get("service_name")
            
            # Check if token is expired
            if exp and datetime.utcnow().timestamp() > exp:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if user_id is None or role is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Return auth info
            auth_info = {
                "user_id": user_id, 
                "role": role,
                "permissions": permissions,
                "service_name": service_name
            }
            
            return auth_info
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    async def verify_role(required_roles: List[str], credentials: HTTPAuthorizationCredentials = Depends(security)):
        """
        Verify that the user has one of the required roles
        """
        auth_info = await AuthMiddleware.verify_token(credentials)
        
        # Special case for service tokens - they have privileged access
        if auth_info["role"] == "service":
            return auth_info
        
        if auth_info["role"] not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return auth_info
    
    @staticmethod
    async def verify_permission(required_permission: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """
        Verify that the user has a specific permission
        """
        auth_info = await AuthMiddleware.verify_token(credentials)
        
        # Services with the specific permission
        if auth_info["role"] == "service" and required_permission in auth_info.get("permissions", []):
            return auth_info
        
        # Mentors have all permissions
        if auth_info["role"] == "mentor":
            return auth_info
        
        # Add more role-based permission checks here
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    @staticmethod
    async def verify_user_access(user_id: int, allow_mentors: bool = True, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """
        Verify that the user has access to a specific user's data
        - Either they are the user themselves
        - Or they are a mentor (if allow_mentors is True)
        - Or they are a service with appropriate permissions
        """
        auth_info = await AuthMiddleware.verify_token(credentials)
        
        # Allow service tokens with 'read:users' permission
        if auth_info["role"] == "service" and "read:users" in auth_info.get("permissions", []):
            return auth_info
            
        if int(auth_info["user_id"]) != user_id and (not allow_mentors or auth_info["role"] != "mentor"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return auth_info

# Example of how to use this middleware in a dependency
async def require_authenticated(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await AuthMiddleware.verify_token(credentials)

async def require_mentor(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await AuthMiddleware.verify_role(["mentor"], credentials)

async def require_service(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Require a service token"""
    auth_info = await AuthMiddleware.verify_token(credentials)
    if auth_info["role"] != "service":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires a service token",
        )
    return auth_info

async def require_write_tasks_permission(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Require 'write:tasks' permission"""
    return await AuthMiddleware.verify_permission("write:tasks", credentials)

async def require_user_access(user_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify that the user has access to a specific user's data
    """
    auth_info = await AuthMiddleware.verify_token(credentials)
    
    # Allow services with read:users permission
    if auth_info["role"] == "service" and "read:users" in auth_info.get("permissions", []):
        return auth_info
    
    if int(auth_info["user_id"]) != user_id and auth_info["role"] != "mentor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )
    return auth_info
