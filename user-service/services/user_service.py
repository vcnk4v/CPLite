from typing import List, Optional, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.user_model import User, UserRole


class UserService:
    """
    Service for user-related business logic
    """

    @staticmethod
    def get_user_by_id(user_id: int, db: Session) -> User:
        """
        Get a user by ID

        Args:
            user_id: User ID
            db: Database session

        Returns:
            User object

        Raises:
            HTTPException: If user not found
        """
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    @staticmethod
    def get_current_user_profile(user_id: int, db: Session) -> User:
        """
        Get the current user's profile

        Args:
            user_id: Current user ID
            db: Database session

        Returns:
            User object

        Raises:
            HTTPException: If user not found
        """
        return UserService.get_user_by_id(user_id, db)

    @staticmethod
    def update_user_profile(
        user_id: int, update_data: Dict[str, Any], db: Session
    ) -> User:
        """
        Update a user's profile

        Args:
            user_id: User ID
            update_data: Data to update
            db: Database session

        Returns:
            Updated User object

        Raises:
            HTTPException: If user not found or update fails
        """
        user = UserService.get_user_by_id(user_id, db)

        # Update fields if provided
        if "name" in update_data and update_data["name"] is not None:
            user.name = update_data["name"]

        if (
            "codeforces_handle" in update_data
            and update_data["codeforces_handle"] is not None
        ):
            # Check if another user already has this handle
            existing_user = (
                db.query(User)
                .filter(
                    User.codeforces_handle == update_data["codeforces_handle"],
                    User.id != user.id,
                )
                .first()
            )

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Codeforces handle already in use",
                )

            user.codeforces_handle = update_data["codeforces_handle"]

        if "url" in update_data and update_data["url"] is not None:
            user.url = update_data["url"]

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def get_users(role: Optional[UserRole], db: Session) -> List[User]:
        """
        Get users, optionally filtered by role

        Args:
            role: Optional role filter
            db: Database session

        Returns:
            List of User objects
        """
        query = db.query(User)

        if role:
            query = query.filter(User.role == role)

        return query.all()

    @staticmethod
    def link_codeforces_handle(
        user_id: int, codeforces_handle: str, db: Session
    ) -> User:
        """
        Link a Codeforces handle to a user's account

        Args:
            user_id: User ID
            codeforces_handle: Codeforces handle to link
            db: Database session

        Returns:
            Updated User object

        Raises:
            HTTPException: If user not found or handle already in use
        """
        user = UserService.get_user_by_id(user_id, db)

        # Check if another user already has this handle
        existing_user = (
            db.query(User)
            .filter(User.codeforces_handle == codeforces_handle, User.id != user.id)
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Codeforces handle already in use",
            )

        # TODO: Verify the handle via Codeforces API
        # This would typically involve a verification process to ensure
        # the user actually owns the handle

        user.codeforces_handle = codeforces_handle
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def update_user_profile(user_id: int, update_data: dict, db: Session) -> User:
        """
        Update a user's profile

        Args:
            user_id: ID of the user to update
            update_data: Dictionary containing the fields to update
            db: Database session

        Returns:
            Updated user object

        Raises:
            HTTPException: If user not found or validation error
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Handle role update specifically
        if "role" in update_data:
            # If a user already has a role, we might want to add validation logic here
            # For example, prevent changing from mentor to learner if the mentor has active mentees
            if user.role and user.role != update_data["role"]:
                # Check if this is a viable role change
                # This is where you'd add business logic about role transitions if needed
                pass

            user.role = update_data["role"]

        # Handle other fields
        if "name" in update_data:
            user.name = update_data["name"]

        if "codeforces_handle" in update_data:
            # You may want to add validation for Codeforces handle here
            # For example, check if it exists via Codeforces API
            user.codeforces_handle = update_data["codeforces_handle"]

        if "url" in update_data:
            user.url = update_data["url"]

        # Save changes
        db.commit()
        db.refresh(user)
        return user
