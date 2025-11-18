# app/services/codeforces.py

import requests
import time
import hashlib
import random
import string
from collections import defaultdict
import requests
import datetime
import requests
import datetime
from utils.messaging import RabbitMQClient


class CodeforcesAPI:
    def __init__(self, api_key, secret, gemini_api_key=None):
        self.api_key = api_key
        self.secret = secret
        self.base_url = "https://codeforces.com/api/"
        # self.redis_client = Redis(
        #     host=os.getenv("REDIS_HOST", "redis"),
        #     port=int(os.getenv("REDIS_PORT", "6379")),
        #     password=os.getenv("REDIS_PASSWORD", ""),
        # )

    def _generate_signature(self, method, params):
        # Add API key to params
        params["apiKey"] = self.api_key

        # Generate random string
        rand = "".join(
            random.choice(string.ascii_lowercase + string.digits) for _ in range(6)
        )

        # Current unix time
        current_time = int(time.time())

        # Generate signature string
        param_strings = []
        for key in sorted(params.keys()):
            param_strings.append(f"{key}={params[key]}")

        signature_string = f"{rand}/{method}?{'&'.join(param_strings)}#{self.secret}"

        # Create SHA512 hash
        hash_object = hashlib.sha512(signature_string.encode())
        api_sig = hash_object.hexdigest()

        # Add apiSig to params
        params["apiSig"] = rand + api_sig
        params["time"] = current_time

        return params

    def get_user_info(self, handles):
        """Get basic information about users."""
        method = "user.info"
        params = {"handles": handles}

        # For user.info, you don't actually need to sign the request
        url = f"{self.base_url}{method}?handles={handles}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user info: {e}")
            return None

    def get_user_status(self, handle, count=100):
        """Get user's submissions."""
        method = "user.status"
        url = f"{self.base_url}{method}?handle={handle}&count={count}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user status: {e}")
            return None

    def get_contest_problems(self, tags=None, count=100):
        """Get problems from recent contests."""
        # method = "problemset.problems"
        # url = f"{self.base_url}{method}"

        # try:
        #     response = requests.get(url)
        #     response.raise_for_status()
        #     return response.json()
        # except requests.exceptions.RequestException as e:
        #     print(f"Error fetching problems: {e}")
        #     return None
        method = "problemset.problems"
        # params = {"tags": tags}
        # tags are semicol separated
        tags_joined = ";".join(tags) if tags else ""
        url = f"{self.base_url}{method}?{tags_joined}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching problems: {e}")
            return None

    def get_problem_stats(self, handle, submission_count=500):
        """Analyze user's submissions and extract problem statistics."""
        submissions = self.get_user_status(handle, count=submission_count)

        if not submissions or submissions.get("status") != "OK":
            return None

        problems_solved = {}
        attempted_problems = set()

        for submission in submissions["result"]:
            problem = submission["problem"]
            problem_id = (
                f"{problem.get('contestId', 'Unknown')}{problem.get('index', '')}"
            )

            # Track all attempted problems
            attempted_problems.add(problem_id)

            if (
                submission.get("verdict") == "OK" and problem_id not in problems_solved
            ):  # Accepted solution
                problems_solved[problem_id] = {
                    "name": problem.get("name", "Unknown"),
                    "difficulty": problem.get("rating", 0),
                    "tags": problem.get("tags", []),
                    "submission_time": submission.get("creationTimeSeconds", 0),
                    "contest_id": problem.get("contestId", "Unknown"),
                    "index": problem.get("index", ""),
                }

        return problems_solved, attempted_problems

    def get_difficulty_category(self, rating):
        """Categorize problem difficulty."""
        if rating == 0 or rating is None:
            return "Unknown"
        elif rating < 1300:
            return "Easy"
        elif rating < 1800:
            return "Medium"
        else:
            return "Hard"

    def get_attempted_unsolved_problems(self, handle, submission_count=500):
        """
        Get a list of problems that the user has attempted but not solved.

        Args:
            handle (str): Codeforces username
            submission_count (int): Number of submissions to analyze

        Returns:
            list: List of attempted but unsolved problems with details
        """
        submissions = self.get_user_status(handle, count=submission_count)

        if not submissions or submissions.get("status") != "OK":
            return []

        # Track problems by their ID
        problem_status = {}  # Maps problem_id to {"solved": bool, "details": {...}}

        for submission in submissions["result"]:
            problem = submission["problem"]
            problem_id = (
                f"{problem.get('contestId', 'Unknown')}{problem.get('index', '')}"
            )

            # If we haven't seen this problem before, initialize it
            if problem_id not in problem_status:
                problem_status[problem_id] = {
                    "solved": False,
                    "details": {
                        "name": problem.get("name", "Unknown"),
                        "difficulty": problem.get("rating", 0),
                        "tags": problem.get("tags", []),
                        "contest_id": problem.get("contestId", "Unknown"),
                        "index": problem.get("index", ""),
                        "attempts": 0,
                    },
                }

            # Count this as an attempt
            problem_status[problem_id]["details"]["attempts"] += 1

            # If this submission was accepted, mark the problem as solved
            if submission.get("verdict") == "OK":
                problem_status[problem_id]["solved"] = True

        # Filter for problems that were attempted but not solved
        unsolved_problems = [
            problem_status[prob_id]["details"]
            for prob_id, data in problem_status.items()
            if not data["solved"] and data["details"]["attempts"] > 0
        ]

        # Sort by number of attempts (most attempts first)
        unsolved_problems.sort(key=lambda x: x["attempts"], reverse=True)

        return unsolved_problems

    def get_recommended_unsolved_problems(
        self, handle, user_rating, ai_recs, max_recommendations=20
    ):
        """
        Get a list of unsolved problems based on AI recommendations for
        tags and difficulty levels the user should focus on.

        Args:
            handle (str): Codeforces username
            user_rating (int): User's current Codeforces rating
            max_recommendations (int): Maximum number of problems to recommend

        Returns:
            list: List of recommended problems with details
            dict: The AI recommendations that were used
        """
        # Get user's solved and attempted problems
        solved_problems, attempted_problems = self.get_problem_stats(handle)

        # If we couldn't get problem stats, return empty results
        if solved_problems is None:
            return [], {"error": "Could not retrieve user problem statistics"}

        # Get AI recommendations for tags and difficulty levels
        # ai_recs = self.ai_recommender.get_learning_recommendations(
        #     handle, solved_problems, attempted_problems, user_rating
        # )

        # Get all available problems
        # all_problems = self.get_contest_problems()

        # print(all_problems, ai_recs)
        # if not all_problems or all_problems.get("status") != "OK":
        #     print("Error fetching problems")
        #     return [], ai_recs

        # Extract recommendations
        recommended_tags = [
            rec["tag"] for rec in ai_recs["ai_recs"].get("recommendations", [])
        ]

        all_problems = self.get_contest_problems(recommended_tags)

        if not all_problems or all_problems.get("status") != "OK":
            print("Error fetching problems")
            return [], ai_recs

        # print("all_problems", all_problems)
        # Create difficulty range mapping for each tag
        tag_difficulty_ranges = {}
        # print(ai_recs)
        # print("ai_recs", ai_recs["ai_recs"])
        # print("ai_recs", ai_recs["ai_recs"]["recommendations"])
        # print("ai_recs", ai_recs["ai_recs"].get("recommendations", []))
        for rec in ai_recs["ai_recs"].get("recommendations", []):
            print("rec", rec)
            print("rec", rec["tag"])
            print("rec", rec["min_difficulty"])
            print("rec", rec["max_difficulty"])
            tag_difficulty_ranges[rec["tag"]] = {
                "min": rec["min_difficulty"],
                "max": rec["max_difficulty"],
            }

        # Find suitable problems based on AI recommendations
        recommended_problems = []

        print("starting to find problems")
        for problem in all_problems["result"]["problems"]:
            # print(problem)

            problem_id = (
                f"{problem.get('contestId', 'Unknown')}{problem.get('index', '')}"
            )

            # Skip if already solved or attempted
            if problem_id in attempted_problems:
                continue

            # Get problem details
            tags = problem.get("tags", [])
            rating = problem.get("rating", 0)

            # print(tags)
            # print(recommended_tags)

            # Skip problems without rating
            if not rating:
                continue

            # print("rating", rating, tags, problem_id)
            # Check if problem matches any of the recommended tags and difficulty ranges
            for tag in tags:
                if tag in recommended_tags:
                    # Check if difficulty is in the recommended range for this tag
                    difficulty_range = tag_difficulty_ranges[tag]
                    if difficulty_range["min"] <= rating <= difficulty_range["max"]:
                        recommended_problems.append(
                            {
                                "id": problem_id,
                                "name": problem.get("name", "Unknown"),
                                "difficulty": rating,
                                "difficulty_category": self.get_difficulty_category(
                                    rating
                                ),
                                "tags": tags,
                                "matched_recommendation": tag,
                                "contestId": problem.get("contestId", "Unknown"),
                                "index": problem.get("index", ""),
                            }
                        )
                        break

            # Limit to max_recommendations recommended problems
            if len(recommended_problems) >= max_recommendations:
                break

        # Sort problems by difficulty (easier first)
        recommended_problems.sort(key=lambda x: x["difficulty"])
        print(recommended_problems, ai_recs)
        return recommended_problems, ai_recs

    def fetch_contests(self):
        """
        Fetch the list of upcoming Codeforces contests.

        Returns:
            list: List of upcoming contests with their details
            None: If there was an error fetching the contests
        """
        url = f"{self.base_url}contest.list"

        try:
            response = requests.get(url)
            response.raise_for_status()

            data = response.json()
            if data["status"] == "OK":
                # Filter for future contests (phase="BEFORE")
                upcoming_contests = [
                    c for c in data["result"] if c["phase"] == "BEFORE"
                ]

                # Sort by start time (ascending)
                upcoming_contests.sort(key=lambda x: x["startTimeSeconds"])

                return upcoming_contests
            else:
                print(
                    f"API returned error status: {data.get('comment', 'Unknown error')}"
                )
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching contests: {e}")
            return None

    def publish_upcoming_contests(self):
        """
        Fetch upcoming contests and publish them as notifications through RabbitMQ

        Returns:
            bool: True if successful, False otherwise
        """

        # Fetch the contests
        upcoming_contests = self.fetch_contests()

        if not upcoming_contests:
            return False

        try:
            # Initialize RabbitMQ client
            client = RabbitMQClient()

            # Setup exchange for notifications
            exchange_name = "codeforces_notifications"
            client.setup_exchange(exchange_name)

            # Publish each contest as a notification
            for contest in upcoming_contests:
                # Create notification message
                notification = {
                    "type": "upcoming_contest",
                    "data": contest,
                    "timestamp": datetime.datetime.now().isoformat(),
                }

                # Publish to RabbitMQ
                client.publish(
                    exchange_name=exchange_name,
                    routing_key="notifications.contest.upcoming",
                    message=notification,
                    message_type="contest_notification",
                )

            client.close()
            return True

        except Exception as e:
            print(f"Error publishing contest notifications: {e}")
            return False
