import requests
from redis import Redis
import os
import json


def fetch_and_cache_contests(redis_client):
    """Fetch Codeforces contests and cache them in Redis"""
    cache_key = "codeforces:contests"

    try:
        # Check if we have cached contests
        cached_contests = redis_client.get(cache_key)
        if cached_contests:
            contests = json.loads(cached_contests)
            return contests

        # If not cached or cache expired, fetch from API
        response = requests.get("https://codeforces.com/api/contest.list")
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "OK":
                # Filter for future contests (phase="BEFORE")
                contests = [c for c in data["result"] if c["phase"] == "BEFORE"]

                # Cache for 1 hour
                redis_client.setex(cache_key, 3600, json.dumps(contests))  # 1 hour

                return contests

        return []
    except Exception as e:
        print(f"Error fetching contests: {e}")
        return []


if __name__ == "__main__":
    # Example usage
    redis_client = Redis(host="localhost", port=6379, password="")
    contests = fetch_and_cache_contests(redis_client)
    print(contests)
