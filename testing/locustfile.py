import json
import random
import time
import csv
import os
from locust import HttpUser, task, between, SequentialTaskSet, TaskSet, tag
from locust.exception import StopUser
from datetime import datetime, timedelta

# Token management
TOKEN_FILE = "auth_tokens.csv"

# Configuration
codeforces_handles = ["tourist", "Petr", "Um_nik", "Benq", "ecnerwala", "ksun48", "Radewoosh", "neal"]
problem_names = ["Two Sum", "Reverse String", "Valid Parentheses", "Path Sum", "Merge Intervals", "Word Search"]
problem_tags = ["dynamic programming", "graphs", "data structures", "implementation", "math", "greedy"]

# Token storage
class TokenStore:
    """Store for pre-authenticated tokens"""
    def __init__(self, token_file=TOKEN_FILE):
        self.tokens = []
        self.token_file = token_file
        self.load_tokens()
    
    def load_tokens(self):
        """Load tokens from CSV file"""
        if not os.path.exists(self.token_file):
            print(f"⚠️ Token file {self.token_file} not found! Please run token_collector.py first.")
            # Create example file structure
            with open(self.token_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['access_token', 'refresh_token', 'user_id', 'role'])
                writer.writerow(['example_access_token', 'example_refresh_token', '1', 'learner'])
            return
        
        with open(self.token_file, 'r') as f:
            reader = csv.DictReader(f)
            self.tokens = list(reader)
        
        if not self.tokens:
            print(f"⚠️ No tokens found in {self.token_file}! Please run token_collector.py first.")
    
    def get_token(self, role=None):
        """Get a random token from the store, optionally filtered by role"""
        if not self.tokens:
            return None
            
        if role:
            matching_tokens = [token for token in self.tokens if token['role'] == role]
            if matching_tokens:
                return random.choice(matching_tokens)
                
        # If no role specified or no matching tokens, return any token
        return random.choice(self.tokens)

# Initialize token store
token_store = TokenStore()

class CPLiteUser(HttpUser):
    """Base user class for CPLite load testing"""
    abstract = True  # This is an abstract class, will not spawn users
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    access_token = None
    refresh_token = None
    user_id = None
    user_role = None
    codeforces_handle = None
    mentor_id = None
    learner_id = None
    assigned_tasks = []
    
    def on_start(self):
        """Setup user before starting tasks"""
        # Get a pre-authenticated token
        self.load_stored_token()
        
        if not self.access_token:
            print("⚠️ No authentication token available - cannot run tests")
            raise StopUser()
            
        # Get user profile to confirm token works
        if not self.get_user_profile():
            print("⚠️ Authentication failed - token may be expired")
            raise StopUser()
            
        # Set Codeforces handle for getting recommendations
        self.set_codeforces_handle()
        
        # If mentor, get assigned learners
        if self.user_role == "mentor":
            self.get_mentor_learners()
    
    def load_stored_token(self):
        """Load a stored token from the token store"""
        token_data = token_store.get_token()
        if not token_data:
            return False
        
        self.access_token = token_data['access_token']
        self.refresh_token = token_data['refresh_token']
        self.user_id = token_data['user_id']
        self.user_role = token_data['role']
        return True
    
    def get_auth_headers(self):
        """Get authorization headers with access token"""
        if not self.access_token:
            raise StopUser()
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def refresh_access_token(self):
        """Refresh the access token"""
        if not self.refresh_token:
            raise StopUser()
            
        refresh_data = {"refresh_token": self.refresh_token}
        
        with self.client.post("/api/auth/refresh", json=refresh_data, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                return True
            else:
                response.failure(f"Token refresh failed: {response.status_code}, {response.text}")
                return False
    
    def get_user_profile(self):
        """Get current user profile"""
        with self.client.get("/api/users/me", headers=self.get_auth_headers(), catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.user_id = data["id"]
                self.user_role = data["role"]
                if "codeforces_handle" in data and data["codeforces_handle"]:
                    self.codeforces_handle = data["codeforces_handle"]
                return True
            else:
                response.failure(f"Failed to get user profile: {response.status_code}, {response.text}")
                return False
    
    def set_codeforces_handle(self):
        """Set Codeforces handle for the user"""
        if self.codeforces_handle:
            return
            
        # Select a random Codeforces handle
        self.codeforces_handle = random.choice(codeforces_handles)
        
        with self.client.post(
            "/api/users/link-codeforces",
            headers=self.get_auth_headers(),
            params={"codeforces_handle": self.codeforces_handle},
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to set Codeforces handle: {response.status_code}, {response.text}")
    
    def get_mentor_learners(self):
        """Get learners assigned to the mentor"""
        if self.user_role != "mentor":
            return
            
        with self.client.get(
            f"/api/mentor-relationships/mentor/{self.user_id}/learner-list",
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data["success"] and data["learners"]:
                    # Get a random learner to work with
                    learner = random.choice(data["learners"])
                    self.learner_id = learner["id"]
            else:
                response.failure(f"Failed to get mentor learners: {response.status_code}, {response.text}")
                
    def get_learner_mentor(self):
        """Get mentor assigned to this learner"""
        with self.client.get(
            f"/api/mentor-relationships/learner/{self.user_id}/mentor",
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data["success"] and data["mentor_id"]:
                    self.mentor_id = data["mentor_id"]
            else:
                response.failure(f"Failed to get learner's mentor: {response.status_code}, {response.text}")
    
    def get_available_mentors(self):
        """Get available mentors for assignment"""
        if self.user_role != "learner":
            return
            
        with self.client.get(
            "/api/mentor-relationships/mentors/available",
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Get a random mentor to work with
                    mentor = random.choice(data)
                    self.mentor_id = mentor["id"]
            else:
                response.failure(f"Failed to get available mentors: {response.status_code}, {response.text}")
    
    @tag("auth")
    @task(5)
    def refresh_token_task(self):
        """Task to refresh access token"""
        self.refresh_access_token()
    
    @tag("user_profile")
    @task(3)
    def view_user_profile(self):
        """Task to view user profile"""
        with self.client.get("/api/users/me", headers=self.get_auth_headers(), catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get user profile: {response.status_code}, {response.text}")
    
    @tag("codeforces")
    @task(2)
    def get_codeforces_stats(self):
        """Get Codeforces stats for user"""
        if not self.codeforces_handle:
            self.set_codeforces_handle()
            
        with self.client.get(
            f"/api/codeforces/user/{self.codeforces_handle}/stats",
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get Codeforces stats: {response.status_code}, {response.text}")
    
    @tag("codeforces")
    @task(2)
    def get_codeforces_info(self):
        """Get Codeforces info for user"""
        if not self.codeforces_handle:
            self.set_codeforces_handle()
            
        with self.client.get(
            f"/api/codeforces/user/{self.codeforces_handle}",
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get Codeforces info: {response.status_code}, {response.text}")
    
    @tag("notifications")
    @task(3)
    def get_notifications(self):
        """Get user notifications"""
        with self.client.get(
            f"/api/notification/user/{self.user_id}",
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get notifications: {response.status_code}, {response.text}")
    
    @tag("ai")
    @task(1)
    def get_recommendations(self):
        """Get AI recommendations for the user"""
        if not self.codeforces_handle:
            self.set_codeforces_handle()
            
        # Mock request - would need real tag_stats data in production
        recommendation_request = {
            "handle": self.codeforces_handle,
            "user_rating": random.randint(800, 2200),
            "tag_stats": {
                "dynamic programming": {
                    "count": random.randint(1, 50),
                    "total_difficulty": random.randint(1000, 20000),
                    "max_difficulty": random.randint(1000, 3000),
                    "avg_difficulty": random.randint(800, 2500)
                },
                "graphs": {
                    "count": random.randint(1, 30),
                    "total_difficulty": random.randint(1000, 15000),
                    "max_difficulty": random.randint(1000, 3000),
                    "avg_difficulty": random.randint(800, 2500)
                }
            }
        }
        
        with self.client.post(
            "/api/ai/recommendations",
            headers=self.get_auth_headers(),
            json=recommendation_request,
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get AI recommendations: {response.status_code}, {response.text}")


class MentorUser(CPLiteUser):
    """User class simulating mentor behavior"""
    weight = 25  # 25% of users will be mentors
    wait_time = between(3, 8)  # Mentors might take longer between actions
    
    def on_start(self):
        """Setup mentor user before starting tasks"""
        # Get a pre-authenticated token for a mentor
        self.load_stored_token_for_role("mentor")
        
        if not self.access_token:
            print("⚠️ No mentor authentication token available - cannot run tests")
            raise StopUser()
            
        # Get user profile to confirm token works
        if not self.get_user_profile():
            print("⚠️ Authentication failed - token may be expired")
            raise StopUser()
            
        self.set_codeforces_handle()
        self.get_mentor_learners()
        
        # If no learners found, get tasks directly
        if not self.learner_id:
            self.get_assigned_tasks()
    
    def load_stored_token_for_role(self, role):
        """Load a stored token with a specific role from the token store"""
        token_data = token_store.get_token(role)
        
        if not token_data:
            # Fallback to any available token
            return self.load_stored_token()
            
        self.access_token = token_data['access_token']
        self.refresh_token = token_data['refresh_token']
        self.user_id = token_data['user_id']
        self.user_role = token_data['role']
        return True
    
    def get_assigned_tasks(self):
        """Get tasks assigned by this mentor"""
        with self.client.get(
            f"/api/tasks/mentor/{self.user_id}",
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    self.assigned_tasks = data
            else:
                response.failure(f"Failed to get assigned tasks: {response.status_code}, {response.text}")
    
    @tag("mentor", "tasks")
    @task(5)
    def create_task(self):
        """Create a new task for a learner"""
        if not self.learner_id:
            self.get_mentor_learners()
            if not self.learner_id:
                return
        
        # Create new task
        task_data = {
            "userid": self.learner_id,
            "mentorid": self.user_id,
            "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "status": "pending",
            "problem_name": random.choice(problem_names),
            "difficulty": random.randint(800, 2500),
            "difficulty_category": random.choice(["Easy", "Medium", "Hard"]),
            "tags": random.sample(problem_tags, k=random.randint(1, 3)),
            "contestid": str(random.randint(1000, 2000)),
            "index": random.choice(["A", "B", "C", "D", "E"])
        }
        
        with self.client.post(
            "/api/tasks/",
            headers=self.get_auth_headers(),
            json=task_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.assigned_tasks.append(data)
            else:
                response.failure(f"Failed to create task: {response.status_code}, {response.text}")
    
    @tag("mentor", "tasks")
    @task(3)
    def assign_tasks(self):
        """Assign tasks to learners"""
        # First get tasks that haven't been assigned yet
        self.get_assigned_tasks()
        
        unassigned_tasks = [task for task in self.assigned_tasks if not task["hasbeensubmittedbymentor"]]
        if not unassigned_tasks:
            return
            
        # Select up to 3 tasks to assign
        tasks_to_assign = random.sample(unassigned_tasks, min(3, len(unassigned_tasks)))
        task_assignments = [
            {
                "task_id": task["id"],
                "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            }
            for task in tasks_to_assign
        ]
        
        if not task_assignments:
            return
            
        with self.client.post(
            "/api/tasks/assign",
            headers=self.get_auth_headers(),
            json=task_assignments,
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to assign tasks: {response.status_code}, {response.text}")
    
    @tag("mentor", "tasks")
    @task(4)
    def view_learner_tasks(self):
        """View tasks assigned to a learner"""
        if not self.learner_id:
            self.get_mentor_learners()
            if not self.learner_id:
                return
                
        with self.client.get(
            f"/api/tasks/user/{self.learner_id}",
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to view learner tasks: {response.status_code}, {response.text}")
    
    @tag("mentor", "relationships")
    @task(1)
    def assign_mentor(self):
        """Assign a mentor to a learner"""
        if not self.learner_id:
            self.get_mentor_learners()
            if not self.learner_id:
                return
                
        assignment_data = {
            "learner_id": self.learner_id,
            "mentor_id": self.user_id
        }
        
        with self.client.post(
            "/api/mentor-relationships/assign-mentor",
            headers=self.get_auth_headers(),
            json=assignment_data,
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to assign mentor: {response.status_code}, {response.text}")


class LearnerUser(CPLiteUser):
    """User class simulating learner behavior"""
    weight = 75  # 75% of users will be learners
    wait_time = between(2, 5)  # Learners might access more frequently
    
    def on_start(self):
        """Setup learner user before starting tasks"""
        # Get a pre-authenticated token for a learner
        self.load_stored_token_for_role("learner")
        
        if not self.access_token:
            print("⚠️ No learner authentication token available - cannot run tests")
            raise StopUser()
            
        # Get user profile to confirm token works
        if not self.get_user_profile():
            print("⚠️ Authentication failed - token may be expired")
            raise StopUser()
            
        self.set_codeforces_handle()
        self.get_learner_mentor()
        self.get_assigned_tasks()
    
    def load_stored_token_for_role(self, role):
        """Load a stored token with a specific role from the token store"""
        token_data = token_store.get_token(role)
        
        if not token_data:
            # Fallback to any available token
            return self.load_stored_token()
            
        self.access_token = token_data['access_token']
        self.refresh_token = token_data['refresh_token']
        self.user_id = token_data['user_id']
        self.user_role = token_data['role']
        return True
    
    def get_assigned_tasks(self):
        """Get tasks assigned to this learner"""
        with self.client.get(
            f"/api/tasks/user/{self.user_id}",
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    self.assigned_tasks = data
            else:
                response.failure(f"Failed to get assigned tasks: {response.status_code}, {response.text}")
    
    @tag("learner", "tasks")
    @task(5)
    def view_tasks(self):
        """View tasks assigned to the learner"""
        with self.client.get(
            f"/api/tasks/user/{self.user_id}",
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to view tasks: {response.status_code}, {response.text}")
    
    @tag("learner", "tasks")
    @task(3)
    def update_task_status(self):
        """Update the status of an assigned task"""
        if not self.assigned_tasks:
            self.get_assigned_tasks()
            if not self.assigned_tasks:
                return
                
        # Select a random task to update
        task = random.choice(self.assigned_tasks)
        
        update_data = {
            "status": random.choice(["completed", "pending"])
        }
        
        with self.client.put(
            f"/api/tasks/{task['id']}",
            headers=self.get_auth_headers(),
            json=update_data,
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to update task status: {response.status_code}, {response.text}")
    
    @tag("learner", "codeforces")
    @task(2)
    def get_codeforces_recommendations(self):
        """Get Codeforces recommendations for the user"""
        if not self.codeforces_handle:
            self.set_codeforces_handle()
            
        with self.client.post(
            f"/api/codeforces/user/{self.codeforces_handle}/recommendations",
            headers=self.get_auth_headers(),
            json={
                "user_rating": random.randint(800, 2200),
                "ai_recs": {
                    "ai_recs": {
                        "recommendations": [
                            {"tag": "dynamic programming", "min_difficulty": 1400, "max_difficulty": 1700},
                            {"tag": "graphs", "min_difficulty": 1300, "max_difficulty": 1600}
                        ]
                    }
                }
            },
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get Codeforces recommendations: {response.status_code}, {response.text}")
    
    @tag("learner", "ai")
    @task(1)
    def get_weekly_summary(self):
        """Get AI weekly summary for the user"""
        if not self.codeforces_handle:
            self.set_codeforces_handle()
            
        with self.client.get(
            f"/api/ai/user/{self.codeforces_handle}/weekly-summary",
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get weekly summary: {response.status_code}, {response.text}")
                
    @tag("learner", "notifications")
    @task(4)
    def read_notification(self):
        """Mark a notification as read"""
        # First get notifications
        with self.client.get(
            f"/api/notification/user/{self.user_id}",
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                notifications = response.json()
                if not notifications or len(notifications) == 0:
                    return
                    
                # Select a random unread notification
                unread_notifications = [n for n in notifications if not n["is_read"]]
                if not unread_notifications:
                    return
                    
                notification = random.choice(unread_notifications)
                
                # Mark as read
                with self.client.put(
                    f"/api/notification/{notification['id']}/read",
                    headers=self.get_auth_headers(),
                    catch_response=True
                ) as read_response:
                    if read_response.status_code != 200:
                        read_response.failure(f"Failed to mark notification as read: {read_response.status_code}, {read_response.text}")
            else:
                response.failure(f"Failed to get notifications: {response.status_code}, {response.text}")