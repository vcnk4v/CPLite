import os
import logging
import asyncio
import httpx
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("recommendation_service.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("recommendation_service")

# Service URLs from environment variables
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
TASK_SERVICE_URL = os.getenv("TASK_SERVICE_URL", "http://task-service:8000")
CODEFORCES_SERVICE_URL = os.getenv(
    "CODEFORCES_SERVICE_URL", "http://codeforces-service:8000"
)
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-service:8000")

# Service token for authentication
SERVICE_TOKEN = os.getenv("SERVICE_TOKEN")


async def get_auth_token():
    """
    Get a service authentication token.
    In production, you might want to use a more secure method to obtain the token.
    """
    # if SERVICE_TOKEN:
    #     return SERVICE_TOKEN

    # If no token is provided in environment variables, attempt to get one
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{USER_SERVICE_URL}/auth/service-token",
                json={
                    "service_name": "recommendation_service",
                    "service_secret": os.getenv(
                        "RECOMMENDATION_SERVICE_SECRET", "your-service-secret"
                    ),
                },
            )

            if response.status_code == 200:
                token_data = response.json()
                return token_data.get("access_token")
            else:
                logger.error(f"Failed to obtain service token: {response.text}")
                return None
    except Exception as e:
        logger.error(f"Error getting service token: {str(e)}")
        return None


async def get_all_users(token):
    """Fetch all users with Codeforces handles from the user service."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get(f"{USER_SERVICE_URL}/users/", headers=headers)

            if response.status_code != 200:
                logger.error(
                    f"Failed to get users: {response.status_code} - {response.text}"
                )
                return []

            users = response.json()
            # Filter users with Codeforces handles
            users_with_handles = [
                user
                for user in users
                if user.get("codeforces_handle") and user.get("role") == "learner"
            ]
            logger.info(
                f"Found {len(users_with_handles)} users with Codeforces handles"
            )
            return users_with_handles
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return []


async def get_codeforces_stats(handle):
    """Get Codeforces statistics for a user."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get user info to retrieve rating
            logger.info(
                f"Fetching user info for {handle} from {CODEFORCES_SERVICE_URL}/api/v1/user/{handle}"
            )
            user_info_resp = await client.get(
                f"{CODEFORCES_SERVICE_URL}/api/v1/user/{handle}"
            )
            if user_info_resp.status_code != 200:
                logger.error(
                    f"Failed to get user info for {handle}: {user_info_resp.status_code}"
                )
                return None, None

            user_info = user_info_resp.json()
            user_rating = user_info.get("user_info", {}).get("rating", 0)

            logger.info(f"User {handle} has rating {user_rating}")

            # Get problem statistics
            logger.info(
                f"Fetching stats for user {handle} from {CODEFORCES_SERVICE_URL}/api/v1/user/{handle}/stats"
            )
            stats_resp = await client.get(
                f"{CODEFORCES_SERVICE_URL}/api/v1/user/{handle}/stats"
            )

            if stats_resp.status_code != 200:
                logger.error(
                    f"Failed to get stats for user {handle}: {stats_resp.status_code}"
                )
                return None, None

            stats_data = stats_resp.json()
            return user_rating, stats_data.get("tag_stats", {})
    except Exception as e:
        logger.error(f"Error getting Codeforces stats for {handle}: {str(e)}")
        return None, None


async def get_ai_recommendations(handle, user_rating, tag_stats):
    """Get AI-generated recommendations."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            ai_payload = {
                "handle": handle,
                "user_rating": user_rating,
                "tag_stats": tag_stats,
            }

            ai_resp = await client.post(
                f"{AI_SERVICE_URL}/api/v1/recommendations",
                json=ai_payload,
            )
            if ai_resp.status_code != 200:
                logger.error(
                    f"Failed to get AI recommendations for user {handle}: {ai_resp.status_code}"
                )
                return None

            return ai_resp.json()
    except Exception as e:
        logger.error(f"Error getting AI recommendations for {handle}: {str(e)}")
        return None


async def get_ai_summary(handle):
    """Get AI-generated summary."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:

            ai_resp = await client.get(
                f"{AI_SERVICE_URL}/api/v1/user/{handle}/weekly-summary",
            )
            if ai_resp.status_code != 200:
                logger.error(
                    f"Failed to get AI summary for user {handle}: {ai_resp.status_code}"
                )
                return None

            return ai_resp.json()
    except Exception as e:
        logger.error(f"Error getting AI summary for {handle}: {str(e)}")
        return None


async def get_stats(handle):
    """Get User Statistics."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            ai_resp = await client.get(
                f"{AI_SERVICE_URL}/api/v1/user/{handle}/weekly-stats",
            )
            if ai_resp.status_code != 200:
                logger.error(
                    f"Failed to get AI summary for user {handle}: {ai_resp.status_code}"
                )
                return None

            return ai_resp.json()
    except Exception as e:
        logger.error(f"Error getting AI summary for {handle}: {str(e)}")
        return None


async def get_problem_recommendations(handle, user_rating, ai_recs):
    """Get problem recommendations from Codeforces service."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            final_payload = {"user_rating": user_rating, "ai_recs": ai_recs}

            final_resp = await client.post(
                f"{CODEFORCES_SERVICE_URL}/api/v1/user/{handle}/recommendations",
                json=final_payload,
            )

            if final_resp.status_code != 200:
                logger.error(
                    f"Failed to get final recommendations for user {handle}: {final_resp.status_code}"
                )
                return None

            return final_resp.json()
    except Exception as e:
        logger.error(f"Error getting problem recommendations for {handle}: {str(e)}")
        return None


async def create_tasks(user_id, mentor_id, recommendations, token):
    """Create tasks for a user based on recommendations."""
    try:
        # Set due date to one week from today
        due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        tasks_created = 0
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {token}"}

            for problem in recommendations.get("recommendations", []):
                task_data = {
                    "userid": user_id,
                    "mentorid": mentor_id,
                    "due_date": due_date,
                    "status": "pending",
                    "problem_name": problem.get("name", "Unknown"),
                    "difficulty": problem.get("difficulty"),
                    "difficulty_category": problem.get("difficulty_category"),
                    "tags": problem.get("tags", []),
                    "matched_recommendation": problem.get("matched_recommendation"),
                    "contestid": str(problem.get("contestId", "Unknown")),
                    "index": problem.get("index", ""),
                }

                response = await client.post(
                    f"{TASK_SERVICE_URL}/tasks/", json=task_data, headers=headers
                )

                if response.status_code == 200 or response.status_code == 201:
                    tasks_created += 1
                else:
                    logger.error(
                        f"Failed to create task for user {user_id}: {response.status_code} - {response.text}"
                    )

            logger.info(f"Created {tasks_created} tasks for user {user_id}")
            return tasks_created
    except Exception as e:
        logger.error(f"Error creating tasks for user {user_id}: {str(e)}")
        return 0


async def generate_and_save_summary(
    user_id, mentor_id, user_data, recommendations, token
):
    """Generate and save a summary of the recommendations."""
    try:
        # Build a summary of the recommendations
        handle = user_data.get("codeforces_handle")

        summary = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "mentor_id": mentor_id,
            "codeforces_handle": handle,
            "recommendations": recommendations.get("recommendations", []),
        }

        # For a real application, you would store this in a database
        # Here we're just logging it
        logger.info(f"Summary for user {user_id}: {json.dumps(summary, indent=2)}")

        # In a real scenario, you might save this to the database:
        # async with httpx.AsyncClient() as client:
        #     headers = {"Authorization": f"Bearer {token}"}
        #     await client.post(f"{TASK_SERVICE_URL}/summaries/", json=summary, headers=headers)

        return True
    except Exception as e:
        logger.error(f"Error generating summary for user {user_id}: {str(e)}")
        return False


async def process_user(user, mentors, token):
    """Process a single user to generate recommendations and tasks."""
    user_id = user.get("id")
    handle = user.get("codeforces_handle")

    if not handle:
        logger.warning(f"User {user_id} has no Codeforces handle, skipping...")
        return False

    logger.info(f"Processing user {user_id} with handle {handle}...")

    # Get Codeforces stats
    user_rating, tag_stats = await get_codeforces_stats(handle)
    if user_rating is None or tag_stats is None:
        logger.error(f"Could not get Codeforces stats for user {user_id}, skipping...")
        return False

    # Get AI recommendations
    ai_recs = await get_ai_recommendations(handle, user_rating, tag_stats)
    if not ai_recs:
        logger.error(
            f"Could not get AI recommendations for user {user_id}, skipping..."
        )
        return False

    ai_summary = await get_ai_summary(handle)
    if not ai_summary:
        logger.error(f"Could not get AI summary for user {user_id}, skipping...")
        return False

    ai_stats = await get_stats(handle)
    if not ai_stats:
        logger.error(f"Could not get AI stats for user {user_id}, skipping...")
        return False

    # logger.info(f"AI recommendations for user {user_id}: {json.dumps(ai_recs, indent=2)}")
    # Get problem recommendations
    final_recommendations = await get_problem_recommendations(
        handle, user_rating, ai_recs
    )
    if not final_recommendations:
        logger.error(
            f"Could not get problem recommendations for user {user_id}, skipping..."
        )
        return False

    logger.info(
        f"Final recommendations for user {user_id}: {json.dumps(final_recommendations, indent=2)}"
    )
    # Assign a mentor (for simplicity, we'll use the first mentor in the list)
    # mentor_id = mentors[0].get("id") if mentors else 1
    # mentor_id = 2
    # get mentor id from user service
    mentor_id = await get_mentor_by_user_id(user_id, token)
    if not mentor_id:
        logger.error(f"Could not find a mentor for user {user_id}, skipping...")
        return False
    # Create tasks
    tasks_created = await create_tasks(user_id, mentor_id, final_recommendations, token)

    # Generate and save summary
    await generate_and_save_summary(
        user_id, mentor_id, user, final_recommendations, token
    )

    return tasks_created > 0


async def get_mentors(token):
    """Fetch all mentors from the user service."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get(
                f"{USER_SERVICE_URL}/users/?role=mentor", headers=headers
            )

            if response.status_code != 200:
                logger.error(
                    f"Failed to get mentors: {response.status_code} - {response.text}"
                )
                return []

            mentors = response.json()
            logger.info(f"Found {len(mentors)} mentors")
            return mentors
    except Exception as e:
        logger.error(f"Error fetching mentors: {str(e)}")
        return []


async def get_mentor_by_user_id(user_id, token):
    """Fetch a mentor by user ID from the user service."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get(
                f"{USER_SERVICE_URL}/mentor-relationships/learner/{user_id}/mentor",
                headers=headers,
            )

            if response.status_code != 200:
                logger.error(
                    f"Failed to get mentor for user {user_id}: {response.status_code} - {response.text}"
                )
                return None

            res_json = response.json()
            if not res_json:
                logger.warning(f"No mentor found for user {user_id}")
                return None
            mentor_id = res_json.get("mentor_id")
            if not mentor_id:
                logger.warning(f"No mentor ID found for user {user_id}")
                return None
            return mentor_id
    except Exception as e:
        logger.error(f"Error fetching mentor for user {user_id}: {str(e)}")
        return None


async def process_all_users():
    """Main function to process all users and generate recommendations."""
    start_time = datetime.now()
    logger.info(f"Started recommendation processing at {start_time}")

    # Get service token
    token = await get_auth_token()
    if not token:
        logger.error("Could not get authentication token, exiting...")
        return {"status": "error", "message": "Authentication failed"}

    # Get all users with Codeforces handles
    users = await get_all_users(token)
    if not users:
        logger.error("No users found with Codeforces handles, exiting...")
        return {"status": "error", "message": "No users found"}

    # Get all mentors
    mentors = await get_mentors(token)

    # Process each user
    processed_count = 0
    success_count = 0

    # Process users in batches to avoid overwhelming the system
    batch_size = 5
    for i in range(0, len(users), batch_size):
        batch = users[i : i + batch_size]
        logger.info(
            f"Processing batch {i//batch_size + 1} of {len(users)//batch_size + 1}..."
        )

        # Process users in parallel
        tasks = [process_user(user, mentors, token) for user in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_count += len(batch)
        success_count += sum(1 for r in results if r is True)

        # Add a small delay between batches to avoid rate limiting
        await asyncio.sleep(5)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info(f"Recommendation processing completed at {end_time}")
    logger.info(f"Processed {processed_count} users, {success_count} successfully")
    logger.info(f"Total duration: {duration:.2f} seconds")

    return {
        "status": "success", 
        "processed": processed_count, 
        "successful": success_count,
        "duration_seconds": duration
    }


# If this file is run directly, execute the main function
if __name__ == "__main__":
    try:
        logger.info("Running recommendation service as standalone script")
        asyncio.run(process_all_users())
    except Exception as e:
        logger.error(f"Error in main execution: {e}")