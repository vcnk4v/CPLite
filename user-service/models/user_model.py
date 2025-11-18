import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class UserRole(enum.Enum):
    """User roles enumeration"""
    mentor = "mentor"
    learner = "learner"
    service = "service"

class AuthProvider(enum.Enum):
    """Authentication provider enumeration"""
    google = "google"
    email = "email"
    # Add more providers as needed

class User(Base):
    """User model representing users in the database"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    date_created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    codeforces_handle = Column(String, unique=True, nullable=True)
    url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    # Auth related fields
    auth_provider = Column(Enum(AuthProvider), nullable=False)
    # For OAuth providers, this is the provider's user ID
    provider_user_id = Column(String, nullable=True)
    # For email auth - store hashed password
    password_hash = Column(String, nullable=True)

    # Relationships
    oauth_info = relationship("OAuthInfo", back_populates="user", uselist=False, cascade="all, delete-orphan")


class OAuthInfo(Base):
    """OAuth information model for external authentication providers"""
    __tablename__ = "oauth_info"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(Enum(AuthProvider), nullable=False)
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="oauth_info")
