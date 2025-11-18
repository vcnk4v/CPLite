import os
import json
import requests
import asyncio
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import google.generativeai as genai


class StatsAndSummaryService:
    def __init__(self, api_key=None):
        """Initialize the Stats and Summary Service with Google Gemini API."""
        self.api_key = api_key or os.environ.get(
            "GEMINI_API_KEY", ""
        )  # add your default key if needed
        if not self.api_key:
            raise ValueError("Gemini API key is required")

        # Configure the Gemini API
        genai.configure(api_key=self.api_key)

        # Codeforces API base URL
        self.cf_api_base = "https://codeforces.com/api"

    def fetch_user_submissions(self, handle: str) -> List[Dict]:
        """
        Fetch a user's submissions from the Codeforces API.

        Args:
            handle (str): Codeforces username

        Returns:
            List[Dict]: List of the user's submissions
        """
        try:
            url = f"{self.cf_api_base}/user.status?handle={handle}"
            response = requests.get(url)
            response.raise_for_status()

            data = response.json()
            if data["status"] != "OK":
                return []

            return data["result"]
        except Exception as e:
            print(f"Error fetching user submissions: {str(e)}")
            return []

    def fetch_user_info(self, handle: str) -> Dict:
        """
        Fetch information about a Codeforces user.

        Args:
            handle (str): Codeforces username

        Returns:
            Dict: User information
        """
        try:
            url = f"{self.cf_api_base}/user.info?handles={handle}"
            response = requests.get(url)
            response.raise_for_status()

            data = response.json()
            if data["status"] != "OK" or not data["result"]:
                return {}

            return data["result"][0]
        except Exception as e:
            print(f"Error fetching user info: {str(e)}")
            return {}

    def get_user_problems_past_week(self, handle: str) -> Dict:
        """
        Get a user's solved problems from the past week using the Codeforces API.

        Args:
            handle (str): Codeforces username

        Returns:
            dict: Dictionary containing the user's solved problems
        """
        submissions = self.fetch_user_submissions(handle)
        if not submissions:
            return {}

        # Calculate the date one week ago
        one_week_ago = datetime.now() - timedelta(days=7)

        # Process submissions to extract solved problems from the past week
        solved_problems = {}
        for submission in submissions:
            # Skip if not accepted
            if submission.get("verdict") != "OK":
                continue

            # Check if submission is from the past week
            submission_time = submission.get("creationTimeSeconds", 0)
            submission_date = datetime.fromtimestamp(submission_time)
            if submission_date < one_week_ago:
                continue

            problem = submission.get("problem", {})
            problem_id = f"{problem.get('contestId', 0)}{problem.get('index', '')}"

            # Skip if we've already processed this problem
            if problem_id in solved_problems:
                continue

            # Extract problem data
            solved_problems[problem_id] = {
                "name": problem.get("name", "Unknown"),
                "difficulty": problem.get("rating", 0),
                "tags": problem.get("tags", []),
                "submission_time": submission_time,
            }

        return solved_problems

    def generate_summary(self, handle: str) -> str:
        """
        Generate an AI-powered summary of the user's problem-solving patterns using Gemini API.
        Focused on past week's problems.

        Args:
            handle (str): Codeforces username

        Returns:
            str: AI-generated summary of the user's problem-solving patterns
        """
        try:
            # Get problems solved in the past week
            problems_data = self.get_user_problems_past_week(handle)

            # If no data, return a default message
            if not problems_data:
                return (
                    "No problem-solving data available for this user in the past week."
                )

            # Extract problem statistics for better summarization
            problem_stats = self._analyze_problem_data(problems_data)

            # Get user info for additional context
            user_info = self.fetch_user_info(handle)
            current_rating = user_info.get("rating", "Unknown")
            max_rating = user_info.get("maxRating", "Unknown")
            rank = user_info.get("rank", "Unknown")

            prompt = f"""
            As a coding coach, analyze this CodeForces problem-solving data for user {handle} for the past week and provide a personalized summary.
            Include patterns in problem difficulty, strengths, areas for improvement, 
            and suggestions for next problems to tackle.
            
            User Info:
            - Current Rating: {current_rating}
            - Max Rating: {max_rating}
            - Rank: {rank}
            
            Problem Statistics (Past Week):
            - Total solved problems: {len(problems_data)}
            - Difficulty distribution: {json.dumps(problem_stats['difficulty_distribution'])}
            - Tag distribution: {json.dumps(problem_stats['tag_distribution'])}
            - Recent activity: {json.dumps(problem_stats['recent_activity'])}
            
            Provide analysis in 3-4 paragraphs. Include:
            1. Overview of difficulty distribution and problem tags
            2. Strengths and areas for improvement based on solved problem patterns
            3. Specific recommendations for advancing their skills
            """

            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)

            return response.text

        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return "Unable to generate AI summary due to an error."

    def get_user_progress_stats(self, handle: str) -> Dict:
        """
        Generate statistics about the user's progress over the past week.

        Args:
            handle (str): Codeforces username

        Returns:
            dict: Statistics about the user's progress
        """
        # Get problems solved in the past week
        solved_problems = self.get_user_problems_past_week(handle)

        if not solved_problems:
            return {
                "total_solved": 0,
                "progress_over_time": [],
                "difficulty_distribution": {},
                "tag_distribution": {},
            }

        # Initialize statistics
        stats = {
            "total_solved": len(solved_problems),
            "progress_over_time": [],
            "difficulty_distribution": defaultdict(int),
            "tag_distribution": defaultdict(int),
        }

        # Convert submission times to readable dates and sort by time
        problem_timeline = []
        for problem_id, data in solved_problems.items():
            submission_time = data.get("submission_time", 0)
            if submission_time > 0:
                date = datetime.fromtimestamp(submission_time).strftime("%Y-%m-%d")
                problem_timeline.append(
                    {
                        "date": date,
                        "problem_id": problem_id,
                        "difficulty": data.get("difficulty", 0),
                        "tags": data.get("tags", []),
                    }
                )

        # Sort by submission time
        problem_timeline.sort(key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"))

        # Group problems by date
        problems_by_date = defaultdict(list)
        for problem in problem_timeline:
            problems_by_date[problem["date"]].append(problem)

        # Generate daily progress over time (past week)
        dates = sorted(problems_by_date.keys())
        for date in dates:
            problems = problems_by_date[date]
            stats["progress_over_time"].append(
                {
                    "date": date,
                    "problems_solved": len(problems),
                }
            )

        # Calculate difficulty distribution
        for problem_id, problem_data in solved_problems.items():
            difficulty = problem_data.get("difficulty", 0)
            difficulty_category = self._get_difficulty_category(difficulty)
            stats["difficulty_distribution"][difficulty_category] += 1

        # Calculate tag distribution
        for problem_id, problem_data in solved_problems.items():
            for tag in problem_data.get("tags", []):
                stats["tag_distribution"][tag] += 1

        # Convert defaultdicts to regular dicts for JSON serialization
        stats["difficulty_distribution"] = dict(stats["difficulty_distribution"])
        stats["tag_distribution"] = dict(stats["tag_distribution"])

        return stats

    def _analyze_problem_data(self, solved_problems: Dict) -> Dict:
        """
        Analyze problem data to extract useful statistics for AI analysis.

        Args:
            solved_problems (dict): Dictionary of problems the user has solved

        Returns:
            dict: Statistics about the user's problem-solving patterns
        """
        # Initialize statistics
        stats = {
            "difficulty_distribution": defaultdict(int),
            "tag_distribution": defaultdict(int),
            "recent_activity": [],
        }

        # Process solved problems
        for problem_id, problem_data in solved_problems.items():
            # Difficulty distribution
            difficulty = problem_data.get("difficulty", 0)
            difficulty_category = self._get_difficulty_category(difficulty)
            stats["difficulty_distribution"][difficulty_category] += 1

            # Tag distribution
            for tag in problem_data.get("tags", []):
                stats["tag_distribution"][tag] += 1

            # Recent activity (store all submissions from the past week)
            submission_time = problem_data.get("submission_time", 0)
            if submission_time > 0:
                stats["recent_activity"].append(
                    {
                        "problem_id": problem_id,
                        "name": problem_data.get("name", "Unknown"),
                        "difficulty": difficulty,
                        "tags": problem_data.get("tags", []),
                        "submission_time": submission_time,
                    }
                )

        # Sort recent activity by submission time (newest first)
        stats["recent_activity"].sort(key=lambda x: x["submission_time"], reverse=True)

        # Convert defaultdicts to regular dicts for JSON serialization
        stats["difficulty_distribution"] = dict(stats["difficulty_distribution"])
        stats["tag_distribution"] = dict(stats["tag_distribution"])

        return stats

    def _get_difficulty_category(self, rating: int) -> str:
        """
        Categorize problem difficulty.

        Args:
            rating (int): Problem difficulty rating

        Returns:
            str: Difficulty category (Easy, Medium, Hard, or Unknown)
        """
        if rating == 0 or rating is None:
            return "Unknown"
        elif rating < 1300:
            return "Easy"
        elif rating < 1800:
            return "Medium"
        else:
            return "Hard"
