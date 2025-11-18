from sqlalchemy.orm import Session
from typing import List, Optional, Tuple

from models.user_model import User, UserRole
from models.learner_mentor_model import MentorLearnerRelationship
from schemas.learner_mentor_schemas import MentorResponse


class LearnerMentorService:
    def __init__(self, db: Session):
        self.db = db

    def validate_learner(self, learner_id: int) -> Optional[User]:
        """
        Validate that a user exists, is active, and is a learner
        """
        return (
            self.db.query(User)
            .filter(
                User.id == learner_id,
                User.role == UserRole.learner,
                User.is_active == True,
            )
            .first()
        )

    def validate_mentor(self, mentor_id: int) -> Optional[User]:
        """
        Validate that a user exists, is active, and is a mentor
        """
        return (
            self.db.query(User)
            .filter(
                User.id == mentor_id,
                User.role == UserRole.mentor,
                User.is_active == True,
            )
            .first()
        )

    def get_active_mentor_relationship(
        self, learner_id: int
    ) -> Optional[MentorLearnerRelationship]:
        """
        Get the active mentor relationship for a learner if it exists
        """
        return (
            self.db.query(MentorLearnerRelationship)
            .filter(
                MentorLearnerRelationship.learner_id == learner_id,
                MentorLearnerRelationship.is_active == True,
            )
            .first()
        )

    def deactivate_relationship(self, relationship: MentorLearnerRelationship) -> None:
        """
        Update an existing relationship to inactive
        """
        relationship.is_active = False
        self.db.commit()

    def create_mentor_relationship(
        self, mentor_id: int, learner_id: int
    ) -> MentorLearnerRelationship:
        """
        Create a new mentor-learner relationship
        """
        new_relationship = MentorLearnerRelationship(
            mentor_id=mentor_id, learner_id=learner_id, is_active=True
        )
        self.db.add(new_relationship)
        self.db.commit()
        self.db.refresh(new_relationship)
        return new_relationship

    def assign_mentor_to_learner(
        self, mentor_id: int, learner_id: int
    ) -> Tuple[MentorLearnerRelationship, bool, str]:
        """
        Assign a mentor to a learner, handling validation and existing relationships
        """
        # Validate learner
        learner = self.validate_learner(learner_id)
        if not learner:
            return (
                None,
                False,
                f"User with id {learner_id} not found or is not a learner",
            )

        # Validate mentor
        mentor = self.validate_mentor(mentor_id)
        if not mentor:
            return None, False, f"Mentor with id {mentor_id} not found or is not active"

        # Check if learner already has an active mentor relationship
        existing_relationship = self.get_active_mentor_relationship(learner_id)
        if existing_relationship:
            # Update existing relationship to inactive
            self.deactivate_relationship(existing_relationship)

        # Create a new mentor-learner relationship
        new_relationship = self.create_mentor_relationship(mentor_id, learner_id)
        return new_relationship, True, "Mentor assigned successfully"

    def get_available_mentors(self) -> List[User]:
        """
        Get all available mentors
        """
        return (
            self.db.query(User)
            .filter(User.role == UserRole.mentor, User.is_active == True)
            .all()
        )

    def get_mentor_by_learner_id(
        self, learner_id: int, include_inactive: bool = False
    ) -> Tuple[User, int, bool, str]:
        """
        Get the mentor assigned to a specific learner
        """
        # Verify the learner exists
        learner = (
            self.db.query(User)
            .filter(User.id == learner_id, User.role == UserRole.learner)
            .first()
        )

        if not learner:
            return (
                None,
                None,
                False,
                f"User with id {learner_id} not found or is not a learner",
            )

        # First try to find an active mentor relationship
        relationship = (
            self.db.query(MentorLearnerRelationship)
            .filter(
                MentorLearnerRelationship.learner_id == learner_id,
                MentorLearnerRelationship.is_active == True,
            )
            .first()
        )

        # If no active relationship and include_inactive is True, find the most recent inactive one
        if not relationship and include_inactive:
            relationship = (
                self.db.query(MentorLearnerRelationship)
                .filter(MentorLearnerRelationship.learner_id == learner_id)
                .order_by(MentorLearnerRelationship.date_created.desc())
                .first()
            )

        if not relationship:
            return None, None, False, "No mentor found for this learner"

        # Get mentor details
        mentor = self.db.query(User).filter(User.id == relationship.mentor_id).first()
        return mentor, relationship.mentor_id, True, "Mentor found for learner"

    def get_mentor_learners(self, mentor_id: int) -> Tuple[List[User], bool, str]:
        """
        Get all learners assigned to a specific mentor
        """
        # Verify the mentor exists
        mentor = (
            self.db.query(User)
            .filter(User.id == mentor_id, User.role == UserRole.mentor)
            .first()
        )

        if not mentor:
            return [], False, f"User with id {mentor_id} not found or is not a mentor"

        # Get all active mentor-learner relationships for this mentor
        relationships = (
            self.db.query(MentorLearnerRelationship)
            .filter(
                MentorLearnerRelationship.mentor_id == mentor_id,
                MentorLearnerRelationship.is_active == True,
            )
            .all()
        )

        if not relationships:
            return [], True, "No learners found for this mentor"

        # Extract learner IDs
        learner_ids = [relationship.learner_id for relationship in relationships]

        # Get learner details
        learners = (
            self.db.query(User)
            .filter(User.id.in_(learner_ids), User.is_active == True)
            .all()
        )

        return learners, True, f"Found {len(learners)} learner(s) for mentor"
