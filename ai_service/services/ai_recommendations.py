# app/services/ai_recommendations.py

import os
import json
import google
from google import genai
from typing import Dict, List, Tuple


class AIRecommender:
    def __init__(self, api_key=None):
        """Initialize the AI recommender with Google Gemini API."""
        self.api_key = api_key or os.environ.get(
            "GEMINI_API_KEY", ""
        )  # add your default key if needed
        if not self.api_key:
            raise ValueError("Gemini API key is required")

        # Configure the Gemini API
        # genai.configure(api_key=self.api_key)
        self.llm = genai.Client(api_key=self.api_key)

        # self.model = genai.GenerativeModel("gemini-2.0-flash")

    def get_learning_recommendations(
        self,
        handle: str,
        user_rating: int,
        tag_stats: Dict,
    ) -> Dict[str, List[Dict]]:
        """
        Get personalized recommendations for a user based on their coding history.

        Args:
            handle: The user's Codeforces handle
            solved_problems: Dictionary of problems the user has solved
            user_rating: The user's current Codeforces rating

        Returns:
            Dictionary with recommendations for tags and difficulty levels
        """
        # Extract tag statistics from solved problems
        # tag_stats = self._analyze_tag_performance(solved_problems)

        # Create a prompt for the AI model
        prompt = self._create_recommendation_prompt(handle, tag_stats, user_rating)

        # Get recommendations from Gemini
        # response = self.model.models.generate_content(prompt)
        response = self.llm.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        # Parse the response to extract recommendations
        try:
            recommendations = self._parse_ai_response(response.text)
            return recommendations
        except Exception as e:
            print(f"Error parsing AI recommendations: {e}")
            # Return default recommendations if parsing fails
            return self._get_default_recommendations()

    def _create_recommendation_prompt(
        self, handle: str, tag_stats: Dict, user_rating: int
    ) -> str:
        """Create a prompt for the AI model to generate recommendations."""
        # Format tag statistics for the prompt
        tag_info = []
        for tag, stats in tag_stats.items():
            tag_info.append(
                f"- {tag}: {stats['count']} problems solved, average difficulty {stats['avg_difficulty']:.1f}, max difficulty {stats['max_difficulty']}"
            )

        tag_stats_text = (
            "\n".join(tag_info) if tag_info else "No tag statistics available"
        )

        prompt = f"""
As a competitive programming coach, analyze this Codeforces user's profile and recommend 5 tags and appropriate difficulty levels they should focus on to improve:

User: {handle}
Current rating: {user_rating}

Tag statistics:
{tag_stats_text}

Based on this information, recommend 5 specific tags this user should focus on next, with an appropriate difficulty rating range for each tag. Consider:
1. Tags they haven't practiced enough
2. Tags where they could increase their maximum difficulty
3. Tags that build important competitive programming skills

Format your response as a valid JSON object like:
{{
  "recommendations": [
    {{"tag": "dynamic programming", "min_difficulty": 1400, "max_difficulty": 1700}},
    {{"tag": "graphs", "min_difficulty": 1300, "max_difficulty": 1600}},
    ...
  ]
}}

Only respond with the JSON - do not include explanations or other text.
        """
        return prompt

    def _parse_ai_response(self, response_text: str) -> Dict:
        """Parse the AI response to extract recommendations."""
        # Clean the response text to extract just the JSON
        cleaned_text = response_text.strip()

        # If response is wrapped in code blocks, extract the content
        if "```json" in cleaned_text:
            cleaned_text = cleaned_text.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned_text:
            cleaned_text = cleaned_text.split("```")[1].strip()

        # Parse the JSON response
        recommendations = json.loads(cleaned_text)
        return recommendations

    def _get_default_recommendations(self) -> Dict:
        """Provide default recommendations if AI recommendations fail."""
        return {
            "recommendations": [
                {
                    "tag": "implementation",
                    "min_difficulty": 800,
                    "max_difficulty": 1600,
                },
                {"tag": "math", "min_difficulty": 800, "max_difficulty": 1600},
                {
                    "tag": "data structures",
                    "min_difficulty": 1000,
                    "max_difficulty": 1800,
                },
                {"tag": "greedy", "min_difficulty": 1000, "max_difficulty": 1800},
                {
                    "tag": "dynamic programming",
                    "min_difficulty": 1200,
                    "max_difficulty": 2000,
                },
            ]
        }
