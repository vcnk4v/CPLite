from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from services.learner_mentor_service import LearnerMentorService
from schemas.learner_mentor_schemas import (
    AssignMentorRequest,
    AssignMentorResponse,
    MentorLearnersResponse,
    LearnerMentorResponse,
    MentorResponse,
)

router = APIRouter(prefix="/mentor-relationships", tags=["mentor-relationships"])


def get_learner_mentor_service(db: Session = Depends(get_db)):
    return LearnerMentorService(db)


@router.post("/assign-mentor", response_model=AssignMentorResponse)
async def assign_mentor(
    request: AssignMentorRequest,
    service: LearnerMentorService = Depends(get_learner_mentor_service),
    # token_data: TokenData = Depends(TokenManager.get_current_user)
):
    """
    Assign a specific mentor to a learner
    """
    relationship, success, message = service.assign_mentor_to_learner(
        mentor_id=request.mentor_id, learner_id=request.learner_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        )

    return AssignMentorResponse(
        mentor_id=relationship.mentor_id,
        learner_id=relationship.learner_id,
        success=True,
        message="Mentor assigned successfully",
    )


@router.get("/mentors/available", response_model=List[MentorResponse])
async def get_available_mentors(
    service: LearnerMentorService = Depends(get_learner_mentor_service),
    # token_data: TokenData = Depends(TokenManager.get_current_user)
):
    """
    Get all available mentors

    Returns:
        List of active mentors with their details
    """
    mentors = service.get_available_mentors()

    if not mentors:
        return []

    return [
        MentorResponse(
            id=mentor.id,
            name=mentor.name,
            codeforces_handle=mentor.codeforces_handle,
            url=mentor.url,
            email=mentor.email,
        )
        for mentor in mentors
    ]


@router.get("/learner/{learner_id}/mentor", response_model=LearnerMentorResponse)
async def get_mentor_by_learner_id(
    learner_id: int,
    include_inactive: bool = False,
    service: LearnerMentorService = Depends(get_learner_mentor_service),
    # token_data: TokenData = Depends(TokenManager.get_current_user)
):
    """
    Get the mentor assigned to a specific learner

    Args:
        learner_id: ID of the learner
        include_inactive: Whether to include inactive mentor relationship if no active one exists
        db: Database session

    Returns:
        The mentor assigned to the learner
    """
    mentor, mentor_id, success, message = service.get_mentor_by_learner_id(
        learner_id, include_inactive
    )

    if not success:
        if "not found" in message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            )

    return LearnerMentorResponse(
        learner_id=learner_id,
        mentor_id=mentor_id,
        mentor=mentor,
        success=success,
        message=message,
    )


@router.get("/mentor/{mentor_id}/learner-list", response_model=MentorLearnersResponse)
async def get_mentor_learners(
    mentor_id: int,
    service: LearnerMentorService = Depends(get_learner_mentor_service),
    # Uncomment when authentication is implemented
    # token_data: TokenData = Depends(TokenManager.get_current_user)
):
    """
    Get all learners assigned to a specific mentor

    Args:
        mentor_id: ID of the mentor

    Returns:
        List of active learners assigned to the specified mentor
    """
    learners, success, message = service.get_mentor_learners(mentor_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    return MentorLearnersResponse(success=True, message=message, learners=learners)
