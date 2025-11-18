# app/api/routes.py

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from services.codeforces import CodeforcesAPI
from core.config import settings

# Initialize the router
router = APIRouter()


# Initialize the Codeforces API client
def get_codeforces_client():
    return CodeforcesAPI(
        api_key=settings.CODEFORCES_API_KEY, secret=settings.CODEFORCES_API_SECRET
    )


# Models
class UserInfoResponse(BaseModel):
    status: str
    user_info: Dict[str, Any]


class ProblemStatsResponse(BaseModel):
    status: str
    tag_stats: Dict[str, Dict]


class RecommendedProblemsResponse(BaseModel):
    status: str
    recommendations: List[Dict[str, Any]]


class UnsolvedProblemsResponse(BaseModel):
    status: str
    unsolved_count: int
    problems: List[Dict[str, Any]]


# Routes
@router.get("/user/{handle}", response_model=UserInfoResponse)
async def get_user_info(
    handle: str, client: CodeforcesAPI = Depends(get_codeforces_client)
):
    """Get basic information about a Codeforces user"""
    response = client.get_user_info(handle)

    if not response or response.get("status") != "OK":
        raise HTTPException(
            status_code=404, detail=f"User {handle} not found or API error"
        )

    user = response["result"][0]
    return {
        "status": "success",
        "user_info": {
            "handle": user.get("handle"),
            "rank": user.get("rank", "Unranked"),
            "rating": user.get("rating", 0),
            "max_rating": user.get("maxRating", 0),
            "contribution": user.get("contribution", 0),
            "friend_of_count": user.get("friendOfCount", 0),
            "avatar": user.get("avatar", ""),
            "title_photo": user.get("titlePhoto", ""),
        },
    }


def _analyze_tag_performance(solved_problems: Dict) -> Dict[str, Dict]:
    """Analyze user's performance by problem tags."""
    tag_stats = {}

    for problem_id, problem in solved_problems.items():
        for tag in problem.get("tags", []):
            if tag not in tag_stats:
                tag_stats[tag] = {
                    "count": 0,
                    "total_difficulty": 0,
                    "max_difficulty": 0,
                }

            tag_stats[tag]["count"] += 1
            difficulty = problem.get("difficulty", 0)
            tag_stats[tag]["total_difficulty"] += difficulty
            tag_stats[tag]["max_difficulty"] = max(
                tag_stats[tag]["max_difficulty"], difficulty
            )

    # Calculate average difficulty for each tag
    for tag, stats in tag_stats.items():
        if stats["count"] > 0:
            stats["avg_difficulty"] = stats["total_difficulty"] / stats["count"]
        else:
            stats["avg_difficulty"] = 0

    return tag_stats


@router.get("/user/{handle}/stats", response_model=ProblemStatsResponse)
async def get_user_stats(
    handle: str,
    submission_count: Optional[int] = 500,
    client: CodeforcesAPI = Depends(get_codeforces_client),
):
    """Get problem-solving statistics for a user"""
    problems_data = client.get_problem_stats(handle, submission_count)

    if not problems_data:
        raise HTTPException(
            status_code=404, detail=f"Could not fetch submission data for {handle}"
        )

    problems, attempted_problems = problems_data

    tag_stats = _analyze_tag_performance(problems)

    # # Process difficulty stats
    # difficulty_category_counts = {}

    # # Process tag stats
    # tags_stats = {}

    # for prob_id, prob_data in problems.items():
    #     # Process difficulty
    #     difficulty = prob_data["difficulty"]
    #     category = client.get_difficulty_category(difficulty)

    #     if category not in difficulty_category_counts:
    #         difficulty_category_counts[category] = 0
    #     difficulty_category_counts[category] += 1

    #     # Process tags
    #     for tag in prob_data["tags"]:
    #         if tag not in tags_stats:
    #             tags_stats[tag] = {
    #                 "total": 0,
    #                 "Easy": 0,
    #                 "Medium": 0,
    #                 "Hard": 0,
    #                 "Unknown": 0,
    #             }

    #         tags_stats[tag]["total"] += 1
    #         tags_stats[tag][category] += 1

    return {
        "status": "success",
        "tag_stats": tag_stats,
    }


@router.post(
    "/user/{handle}/recommendations", response_model=RecommendedProblemsResponse
)
async def get_recommendations(
    handle: str,
    user_rating: Optional[int] = None,
    ai_recs: Dict[str, Any] = {},
    client: CodeforcesAPI = Depends(get_codeforces_client),
):
    """Get recommended unsolved problems for a user"""
    # If user_rating is not provided, try to get it from user info
    if user_rating is None:
        user_info = client.get_user_info(handle)
        if user_info and user_info.get("status") == "OK":
            user_rating = user_info["result"][0].get("rating", 0)
        else:
            user_rating = 0

    recommendations, ai = client.get_recommended_unsolved_problems(
        handle, user_rating, ai_recs
    )

    if not recommendations:
        return {"status": "success", "recommendations": []}
    print(recommendations)
    # Make sure each problem has a URL
    for problem in recommendations:
        print(problem)
        contest_id = problem.get("contestId")
        index = problem.get("index")
        problem["url"] = (
            f"https://codeforces.com/problemset/problem/{contest_id}/{index}"
        )

    return {"status": "success", "recommendations": recommendations}


@router.get("/user/{handle}/unsolved", response_model=UnsolvedProblemsResponse)
async def get_unsolved_problems(
    handle: str,
    submission_count: Optional[int] = 500,
    client: CodeforcesAPI = Depends(get_codeforces_client),
):
    """Get problems that the user has attempted but not solved"""
    unsolved_problems = client.get_attempted_unsolved_problems(handle, submission_count)

    if not unsolved_problems:
        return {"status": "success", "unsolved_count": 0, "problems": []}

    return {
        "status": "success",
        "unsolved_count": len(unsolved_problems),
        "problems": unsolved_problems,
    }


@router.get("/contests/upcoming", tags=["contests"])
async def get_upcoming_contests(client: CodeforcesAPI = Depends(get_codeforces_client)):
    """Get the list of upcoming Codeforces contests"""
    contests = client.fetch_contests()

    if not contests:
        return {"status": "success", "contests": []}

    return {"status": "success", "contests_count": len(contests), "contests": contests}


@router.post("/contests/publish-notifications", tags=["contests"])
async def publish_contest_notifications(
    client: CodeforcesAPI = Depends(get_codeforces_client),
):
    """Fetch upcoming contests and publish them as notifications via RabbitMQ"""
    success = client.publish_upcoming_contests()

    if success:
        return {
            "status": "success",
            "message": "Contest notifications published successfully",
        }
    else:
        raise HTTPException(
            status_code=500, detail="Failed to publish contest notifications"
        )
