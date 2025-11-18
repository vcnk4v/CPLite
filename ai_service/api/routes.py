from fastapi import APIRouter, HTTPException, Depends, Body, Query
from typing import Dict, List, Any, Set
from pydantic import BaseModel
from services.ai_recommendations import AIRecommender
from core.config import settings
from services.stats_summary import StatsAndSummaryService
from sqlalchemy.orm import Session
from database.connection import get_db
from models.user_stats import UserStats
from schemas.user_stats import (
    UserStatsDB,
    WeeklySummaryResponse,
    WeeklyStatsResponse,
    UserStatsResponse,
)
import os

router = APIRouter()


class RecommendationRequest(BaseModel):
    handle: str
    user_rating: int
    tag_stats: Dict[str, Dict[str, Any]]


def get_stats_service():
    """
    Dependency to get the StatsAndSummaryService.
    """
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    return StatsAndSummaryService(api_key=gemini_api_key)


def get_ai_recommender():
    """Dependency to get an instance of the AI recommender."""
    try:
        return AIRecommender(api_key=settings.GEMINI_API_KEY)
    except ValueError as e:
        raise HTTPException(
            status_code=500, detail=f"AI service configuration error: {str(e)}"
        )


@router.post("/recommendations", tags=["AI Recommendations"])
async def get_learning_recommendations(
    request: RecommendationRequest = Body(...),
    ai_recommender: AIRecommender = Depends(get_ai_recommender),
):
    """
    Get personalized tag and difficulty recommendations for a user based on their coding history.
    """
    try:
        recommendations = ai_recommender.get_learning_recommendations(
            handle=request.handle,
            user_rating=request.user_rating,
            tag_stats=request.tag_stats,
        )
        return recommendations
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating recommendations: {str(e)}"
        )


@router.get(
    "/user/{handle}/weekly-summary",
    response_model=WeeklySummaryResponse,
    tags=["Weekly Summary"],
)
async def get_weekly_summary(
    handle: str,
    service: StatsAndSummaryService = Depends(get_stats_service),
    db: Session = Depends(get_db),
):
    """
    Get a weekly summary of a user's problem-solving patterns.
    Saves the summary to the database.

    Args:
        handle (str): Codeforces username

    Returns:
        Dict: Weekly summary of the user's problem-solving patterns
    """
    try:
        # Check if user exists
        user_info = service.fetch_user_info(handle)
        if not user_info:
            raise HTTPException(
                status_code=404, detail=f"User {handle} not found on Codeforces"
            )

        # Generate summary
        summary = service.generate_summary(handle)

        # Save to database
        db_user_stats = (
            db.query(UserStats).filter(UserStats.codeforces_handle == handle).first()
        )

        if db_user_stats:
            # Update existing record
            db_user_stats.summary = summary
            db.commit()
        else:
            # Create new record
            db_user_stats = UserStats(codeforces_handle=handle, summary=summary)
            db.add(db_user_stats)
            db.commit()

        return {"handle": handle, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/user/{handle}/weekly-stats",
    response_model=WeeklyStatsResponse,
    tags=["Weekly Stats"],
)
async def get_weekly_stats(
    handle: str,
    service: StatsAndSummaryService = Depends(get_stats_service),
    db: Session = Depends(get_db),
):
    """
    Get weekly statistics about a user's problem-solving progress.
    Saves the stats to the database.

    Args:
        handle (str): Codeforces username

    Returns:
        Dict: Weekly statistics about the user's problem-solving progress
    """
    try:
        # Check if user exists
        user_info = service.fetch_user_info(handle)
        if not user_info:
            raise HTTPException(
                status_code=404, detail=f"User {handle} not found on Codeforces"
            )

        # Get stats
        stats = service.get_user_progress_stats(handle)

        # Save to database
        db_user_stats = (
            db.query(UserStats).filter(UserStats.codeforces_handle == handle).first()
        )

        if db_user_stats:
            # Update existing record
            db_user_stats.stats = stats
            db.commit()
        else:
            # Create new record
            db_user_stats = UserStats(codeforces_handle=handle, stats=stats)
            db.add(db_user_stats)
            db.commit()

        response_data = {
            "handle": handle,
            "user_info": {
                "rating": user_info.get("rating"),
                "max_rating": user_info.get("maxRating"),
                "rank": user_info.get("rank"),
                "contribution": user_info.get("contribution"),
                "friend_of_count": user_info.get("friendOfCount"),
            },
            "stats": stats,
        }
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/user/{handle}/details", response_model=UserStatsResponse, tags=["User Details"]
)
async def get_user_details(
    handle: str,
    service: StatsAndSummaryService = Depends(get_stats_service),
    db: Session = Depends(get_db),
):
    """
    Get combined weekly statistics and summary for a Codeforces user.
    Updates database with both stats and summary.

    Args:
        handle (str): Codeforces username

    Returns:
        Dict: Comprehensive weekly data about the user
    """
    try:
        # Check if user exists
        user_info = service.fetch_user_info(handle)
        if not user_info:
            raise HTTPException(
                status_code=404, detail=f"User {handle} not found on Codeforces"
            )

        # Get problems solved in the past week
        problems = service.get_user_problems_past_week(handle)

        # Generate summary
        summary = service.generate_summary(handle)

        # Get stats
        stats = service.get_user_progress_stats(handle)

        # Save to database
        db_user_stats = (
            db.query(UserStats).filter(UserStats.codeforces_handle == handle).first()
        )

        if db_user_stats:
            # Update existing record
            db_user_stats.summary = summary
            db_user_stats.stats = stats
            db.commit()
        else:
            # Create new record
            db_user_stats = UserStats(
                codeforces_handle=handle, summary=summary, stats=stats
            )
            db.add(db_user_stats)
            db.commit()

        return {
            "handle": handle,
            "user_info": {
                "rating": user_info.get("rating"),
                "max_rating": user_info.get("maxRating"),
                "rank": user_info.get("rank"),
                "contribution": user_info.get("contribution"),
                "friend_of_count": user_info.get("friendOfCount"),
                "registration_time": user_info.get("registrationTimeSeconds"),
                "last_online_time": user_info.get("lastOnlineTimeSeconds"),
            },
            "problems_count": len(problems),
            "summary": summary,
            "stats": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/db/user/{handle}/data", response_model=UserStatsDB, tags=["Database Access"]
)
async def get_user_data_from_db(handle: str, db: Session = Depends(get_db)):
    """
    Retrieve user data directly from the database without regenerating stats or summary.

    Args:
        handle (str): Codeforces username

    Returns:
        UserStatsDB: User data from the database
    """
    db_user_stats = (
        db.query(UserStats).filter(UserStats.codeforces_handle == handle).first()
    )

    if not db_user_stats:
        raise HTTPException(
            status_code=404,
            detail=f"No stored data found for user {handle}. Please generate data first.",
        )

    return db_user_stats


@router.get(
    "/db/user/{handle}/summary",
    response_model=WeeklySummaryResponse,
    tags=["Database Access"],
)
async def get_summary_from_db(handle: str, db: Session = Depends(get_db)):
    """
    Retrieve only the summary for a user from the database.

    Args:
        handle (str): Codeforces username

    Returns:
        Dict: Weekly summary from the database
    """
    db_user_stats = (
        db.query(UserStats).filter(UserStats.codeforces_handle == handle).first()
    )

    if not db_user_stats or not db_user_stats.summary:
        raise HTTPException(
            status_code=404,
            detail=f"No stored summary found for user {handle}. Please generate summary first.",
        )

    return {"handle": handle, "summary": db_user_stats.summary}


@router.get(
    "/db/user/{handle}/stats", response_model=Dict[str, Any], tags=["Database Access"]
)
async def get_stats_from_db(handle: str, db: Session = Depends(get_db)):
    """
    Retrieve only the stats for a user from the database.

    Args:
        handle (str): Codeforces username

    Returns:
        Dict: Weekly stats from the database
    """
    db_user_stats = (
        db.query(UserStats).filter(UserStats.codeforces_handle == handle).first()
    )

    if not db_user_stats or not db_user_stats.stats:
        raise HTTPException(
            status_code=404,
            detail=f"No stored stats found for user {handle}. Please generate stats first.",
        )

    return {"handle": handle, "stats": db_user_stats.stats}
