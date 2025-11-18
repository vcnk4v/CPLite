#!/usr/bin/env python3
"""
CPLite Notification System End-to-End Performance Test

This script measures the time between task assignment and notification insertion in the database,
for comparing RabbitMQ-based and polling-based implementations.

Usage:
  # Run end-to-end test
  python notification_e2e_test.py --implementation rabbitmq
  python notification_e2e_test.py --implementation polling
"""

import os
import time
import json
import argparse
import random
import csv
import psutil
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from locust import HttpUser, task, between, events
from locust.exception import StopUser

# =====================================================================
# Configuration
# =====================================================================

# Database configuration
DB_URL = os.getenv("DB_URL", "postgresql://cplite:cplitepassword@localhost:5434/notification_service_db")

# Test parameters
TOKEN_FILE = os.getenv("TOKEN_FILE", "auth_tokens.csv")
TASK_COUNT = int(os.getenv("TASK_COUNT", "10"))  # Number of tasks to test
DB_CHECK_INTERVAL = float(os.getenv("DB_CHECK_INTERVAL", "0.1"))  # Seconds between DB checks
MAX_WAIT_TIME = int(os.getenv("MAX_WAIT_TIME", "30"))  # Maximum seconds to wait for notification

# Test data
PROBLEM_NAMES = ["Two Sum", "Reverse String", "Valid Parentheses", "Path Sum", "Merge Intervals", "Word Search"]
PROBLEM_TAGS = ["dynamic programming", "graphs", "data structures", "implementation", "math", "greedy"]

# =====================================================================
# Database connection
# =====================================================================

class NotificationDB:
    """Database connection for checking notifications"""
    
    def __init__(self, db_url=DB_URL):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Test connection to warm up the pool
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to database and warm up connection pool"""
        try:
            session = self.Session()
            session.execute(text("SELECT 1"))
            session.close()
            print("✅ Database connection established")
        except Exception as e:
            print(f"⚠️ Database connection error: {e}")
    
    def check_notification(self, task_id):
        """
        Check if notification exists for the given task ID
        
        Returns:
            dict or None: Notification data if found, None otherwise
        """
        # Create a fresh session for each check (avoid stale data)
        session = self.Session()
        try:
            # Try both approaches to avoid caching issues
            
            # First try direct SQL that bypasses most caching
            query1 = text(f"""
                SELECT id, user_id, content, related_type, related_id, created_at, is_read 
                FROM notification 
                WHERE related_type = 'task' AND related_id = '{task_id}'
            """)
            
            result = session.execute(query1).fetchone()
            
            if not result:
                # Try alternate method with bind parameters
                query2 = text("""
                    SELECT id, user_id, content, related_type, related_id, created_at, is_read 
                    FROM notification 
                    WHERE related_type = 'task' AND related_id = :task_id
                """)
                
                result = session.execute(query2, {"task_id": str(task_id)}).fetchone()
            
            if result:
                # Convert to dict
                notification = {
                    "id": result[0],
                    "user_id": result[1],
                    "content": result[2],
                    "related_type": result[3],
                    "related_id": result[4],
                    "created_at": result[5],
                    "is_read": result[6]
                }
                return notification
            return None
        finally:
            session.close()

# =====================================================================
# Token management
# =====================================================================

class TokenStore:
    """Store for pre-authenticated tokens"""
    
    def __init__(self, token_file=TOKEN_FILE):
        self.tokens = []
        self.token_file = token_file
        self.load_tokens()
    
    def load_tokens(self):
        """Load tokens from CSV file"""
        if not os.path.exists(self.token_file):
            print(f"⚠️ Token file {self.token_file} not found!")
            return
        
        try:
            with open(self.token_file, 'r') as f:
                reader = csv.DictReader(f)
                self.tokens = list(reader)
            
            if not self.tokens:
                print(f"⚠️ No tokens found in {self.token_file}!")
            else:
                print(f"✅ Loaded {len(self.tokens)} tokens from {self.token_file}")
                # Print sample token (masked)
                if self.tokens and 'access_token' in self.tokens[0]:
                    token = self.tokens[0]['access_token']
                    masked = token[:10] + "..." + token[-5:] if len(token) > 15 else "***masked***"
                    print(f"Sample token: {masked}")
        except Exception as e:
            print(f"⚠️ Error loading tokens: {e}")
            self.tokens = []
    
    def get_token(self, role=None):
        """Get a token for the specified role"""
        if not self.tokens:
            return None
            
        if role:
            matching_tokens = [token for token in self.tokens if token['role'] == role]
            if matching_tokens:
                return random.choice(matching_tokens)
                
        # Fallback to any token
        return random.choice(self.tokens)

# =====================================================================
# Performance tracking
# =====================================================================

class PerformanceTracker:
    """Tracks and reports on notification performance"""
    
    def __init__(self, implementation):
        self.implementation = implementation
        self.tasks = {}  # {task_id: {"assigned_at": timestamp, "notification_at": timestamp}}
        self.notification_times = []  # List of notification times in ms
        self.test_start_time = time.time()  # Track when the test started
        self.test_end_time = None
        self.task_creation_times = []  # Track task creation times
        self.task_assignment_times = []  # Track task assignment times
        self.db_check_counts = {}  # {task_id: check_count} - track DB checks needed per notification
        self.total_db_checks = 0  # Total number of database checks
        
        # Resource monitoring
        self.cpu_samples = []
        self.memory_samples = []
        self.last_resource_sample_time = time.time()
        self.resource_sample_interval = 1.0  # seconds
    
    def track_task_creation(self, task_id, creation_time_ms):
        """Record task creation time"""
        self.task_creation_times.append(creation_time_ms)
        self._sample_resource_usage()
    
    def track_task_assignment(self, task_id):
        """Record task assignment time"""
        assignment_time = time.time()
        self.tasks[task_id] = {
            "assigned_at": assignment_time,
            "notification_at": None,
            "db_check_count": 0  # Initialize database check count
        }
        self._sample_resource_usage()
        return assignment_time
    
    def increment_db_check_count(self, task_id):
        """Increment the database check count for a task"""
        if task_id in self.tasks:
            self.tasks[task_id]["db_check_count"] = self.tasks[task_id].get("db_check_count", 0) + 1
            self.total_db_checks += 1
    
    def track_notification_received(self, task_id):
        """Record notification time and calculate delivery time"""
        if task_id in self.tasks and self.tasks[task_id]["assigned_at"]:
            self.tasks[task_id]["notification_at"] = time.time()
            
            # Calculate delivery time
            delivery_time = (self.tasks[task_id]["notification_at"] - 
                           self.tasks[task_id]["assigned_at"]) * 1000  # ms
            
            self.notification_times.append(delivery_time)
            
            # Store DB check count in a separate dict for easy access
            self.db_check_counts[task_id] = self.tasks[task_id].get("db_check_count", 0)
            
            self._sample_resource_usage()
            return delivery_time
        return None
    
    def _sample_resource_usage(self):
        """Take a sample of CPU and memory usage"""
        current_time = time.time()
        if current_time - self.last_resource_sample_time >= self.resource_sample_interval:
            process = psutil.Process(os.getpid())
            
            # CPU usage (percent)
            cpu_percent = process.cpu_percent(interval=0.1)
            self.cpu_samples.append((current_time, cpu_percent))
            
            # Memory usage (MB)
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            self.memory_samples.append((current_time, memory_mb))
            
            self.last_resource_sample_time = current_time
    
    def finish_test(self):
        """Mark the end of the test for throughput calculations"""
        self.test_end_time = time.time()
        self._sample_resource_usage()
    
    def get_report(self):
        """Generate performance report"""
        # If we haven't explicitly marked the end, do it now
        if not self.test_end_time:
            self.finish_test()
            
        if not self.notification_times:
            return {
                "implementation": self.implementation,
                "status": "No notifications recorded",
                "timestamp": datetime.now().isoformat()
            }
        
        # Calculate test duration
        test_duration_sec = self.test_end_time - self.test_start_time
        
        # Calculate statistics
        notification_times = sorted(self.notification_times)
        sample_count = len(notification_times)
        total_tasks = len(self.tasks)
        avg_time = sum(notification_times) / sample_count if sample_count > 0 else 0
        min_time = min(notification_times) if notification_times else 0
        max_time = max(notification_times) if notification_times else 0
        
        # Calculate throughput
        throughput = sample_count / test_duration_sec if test_duration_sec > 0 else 0
        
        # Calculate database check efficiency
        avg_checks_per_notification = self.total_db_checks / sample_count if sample_count > 0 else 0
        
        # Calculate percentiles
        p50 = notification_times[int(sample_count * 0.5)] if sample_count > 1 else avg_time
        p75 = notification_times[int(sample_count * 0.75)] if sample_count > 1 else avg_time
        p90 = notification_times[int(sample_count * 0.9)] if sample_count > 1 else avg_time
        p95 = notification_times[int(sample_count * 0.95)] if sample_count > 1 else avg_time
        p99 = notification_times[int(sample_count * 0.99)] if sample_count > 1 else avg_time
        
        # Calculate additional metrics if we have task creation times
        creation_stats = {}
        if self.task_creation_times:
            creation_stats = {
                "average_ms": sum(self.task_creation_times) / len(self.task_creation_times),
                "min_ms": min(self.task_creation_times),
                "max_ms": max(self.task_creation_times)
            }
        
        # Process resource usage data
        cpu_stats = {}
        memory_stats = {}
        
        if self.cpu_samples:
            cpu_values = [sample[1] for sample in self.cpu_samples]
            cpu_stats = {
                "average_percent": sum(cpu_values) / len(cpu_values),
                "max_percent": max(cpu_values),
                "min_percent": min(cpu_values)
            }
        
        if self.memory_samples:
            memory_values = [sample[1] for sample in self.memory_samples]
            memory_stats = {
                "average_mb": sum(memory_values) / len(memory_values),
                "max_mb": max(memory_values),
                "min_mb": min(memory_values),
                "peak_mb": max(memory_values)
            }
        
        # Build the report
        return {
            "implementation": self.implementation,
            "timestamp": datetime.now().isoformat(),
            "test_duration": {
                "seconds": test_duration_sec,
                "formatted": f"{test_duration_sec:.2f} sec"
            },
            "throughput": {
                "notifications_per_second": throughput,
                "formatted": f"{throughput:.2f} notifications/sec",
                "tasks_per_second": total_tasks / test_duration_sec if test_duration_sec > 0 else 0
            },
            "metrics": {
                "sample_count": sample_count,
                "total_tasks": total_tasks,
                "success_rate": sample_count / total_tasks if total_tasks else 0,
                "notification_times_ms": {
                    "average": avg_time,
                    "min": min_time,
                    "median": p50,
                    "p75": p75,
                    "p90": p90,
                    "p95": p95,
                    "p99": p99,
                    "max": max_time,
                    "std_dev": self._calculate_std_dev(notification_times, avg_time) if notification_times else 0
                }
            },
            "database_checks": {
                "total_checks": self.total_db_checks,
                "average_checks_per_notification": avg_checks_per_notification,
                "check_distribution": self.db_check_counts
            },
            "task_creation_performance": creation_stats,
            "resource_usage": {
                "cpu": cpu_stats,
                "memory": memory_stats,
            },
            "raw_data": {
                "notification_times": self.notification_times,
                "cpu_samples": self.cpu_samples,
                "memory_samples": self.memory_samples
            }
        }
    
    def _calculate_std_dev(self, values, mean):
        """Calculate standard deviation"""
        if not values or len(values) < 2:
            return 0
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def save_report(self, filename=None):
        """Save performance report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"notification_perf_{self.implementation}_{timestamp}.json"
        
        report = self.get_report()
        
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"Report saved to {filename}")
        return filename

# =====================================================================
# E2E Test Implementation
# =====================================================================

class NotificationTestUser(HttpUser):
    """User for testing notification performance"""
    
    wait_time = between(1, 2)  # Wait 1-2 seconds between tasks
    
    # Test attributes
    mentor_token = None
    learner_token = None
    mentor_id = None
    learner_id = None
    task_count = 0
    db = None
    tracker = None
    
    def on_start(self):
        """Setup before starting test"""
        # Load tokens
        token_store = TokenStore()
        
        # Get mentor and learner tokens
        self.mentor_token = token_store.get_token("mentor")
        self.learner_token = token_store.get_token("learner")
        
        if not self.mentor_token or not self.learner_token:
            print("⚠️ Missing required tokens! Need both mentor and learner tokens.")
            raise StopUser()
        
        # Set up user IDs
        self.mentor_id = self.mentor_token["user_id"]
        self.learner_id = self.learner_token["user_id"]
        
        # Initialize DB connection
        self.db = NotificationDB()
        
        # Use shared tracker if available, otherwise create a new one
        if hasattr(self.environment, "shared_tracker"):
            self.tracker = self.environment.shared_tracker
        else:
            self.tracker = PerformanceTracker(getattr(self.environment, "implementation", "unknown"))
        
        print(f"Starting test with mentor ID: {self.mentor_id}, learner ID: {self.learner_id}")
    
    def get_auth_headers(self, is_mentor=True):
        """Get authorization headers for the appropriate user"""
        try:
            token = self.mentor_token if is_mentor else self.learner_token
            if token and 'access_token' in token:
                return {"Authorization": f"Bearer {token['access_token']}"}
            else:
                print("⚠️ Invalid token format:", token)
                return {}
        except Exception as e:
            print(f"⚠️ Error creating auth headers: {e}")
            return {}
    
    def create_task(self):
        """Create a new task as the mentor"""
        try:
            print(f"🔄 Creating task with mentor: {self.mentor_id}, learner: {self.learner_id}")
            
            # Create task data
            task_data = {
                "userid": self.learner_id,
                "mentorid": self.mentor_id,
                "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "status": "pending",
                "problem_name": f"Test Problem {self.task_count} - {random.choice(PROBLEM_NAMES)}",
                "difficulty": random.randint(800, 2500),
                "difficulty_category": random.choice(["Easy", "Medium", "Hard"]),
                "tags": random.sample(PROBLEM_TAGS, k=random.randint(1, 3)),
                "contestid": str(random.randint(1000, 2000)),
                "index": random.choice(["A", "B", "C", "D", "E"])
            }
            
            print(f"📦 Prepared task data: {task_data}")
            
            # Get auth headers
            auth_headers = self.get_auth_headers(is_mentor=True)
            print(f"🔑 Using auth headers: {auth_headers}")
            
            # Create task with timeout
            print("🔄 Sending task creation request...")
            
            # Record start time for task creation
            start_time = time.time()
            
            with self.client.post(
                "/api/tasks/",
                headers=auth_headers,
                json=task_data,
                catch_response=True,
                name="Create Task",
                timeout=10  # Add timeout to prevent hanging
            ) as response:
                print(f"📤 Task creation response: {response.status_code}")
                
                # Calculate creation time
                creation_time = (time.time() - start_time) * 1000  # convert to ms
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        task_id = data["id"]
                        print(f"✅ Created task {task_id}")
                        
                        # Track task creation time
                        self.tracker.track_task_creation(task_id, creation_time)
                        
                        return task_id
                    except Exception as e:
                        print(f"❌ Error parsing task creation response: {e}")
                        print(f"Response content: {response.text}")
                        return None
                else:
                    response.failure(f"Failed to create task: {response.text}")
                    print(f"❌ Task creation failed with status {response.status_code}: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error creating task: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def assign_task(self, task_id):
        """Assign a task and measure notification time"""
        # Create assignment data
        task_assignment = [{
            "task_id": task_id,
            "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        }]
        
        # Assign task
        with self.client.post(
            "/api/tasks/assign",
            headers=self.get_auth_headers(is_mentor=True),
            json=task_assignment,
            catch_response=True,
            name="Assign Task"
        ) as response:
            if response.status_code == 200:
                # Start tracking this task
                assignment_time = self.tracker.track_task_assignment(task_id)
                print(f"📝 Assigned task {task_id} at {datetime.fromtimestamp(assignment_time).strftime('%H:%M:%S.%f')[:-3]}")
                
                # Wait for notification to appear in database
                self.wait_for_notification(task_id)
                return True
            else:
                response.failure(f"Failed to assign task: {response.text}")
                return False
    
    def wait_for_notification(self, task_id):
        """Wait for notification to appear in the database"""
        start_time = time.time()
        found = False
        
        print(f"⏳ Waiting for notification for task {task_id}...")
        
        # First, try a direct check for immediate feedback on first notification
        notification = self.db.check_notification(task_id)
        self.tracker.increment_db_check_count(task_id)  # Count this first db check
        
        if notification:
            delivery_time = self.tracker.track_notification_received(task_id)
            print(f"✉️ Notification received immediately for task {task_id}: {delivery_time:.2f} ms")
            return True
        
        # Then start the checking loop
        check_count = 1  # We already did one check
        while time.time() - start_time < MAX_WAIT_TIME:
            check_count += 1
            self.tracker.increment_db_check_count(task_id)  # Track each db check
            
            # Check database for notification
            notification = self.db.check_notification(task_id)
            
            if notification:
                # Calculate and record delivery time
                delivery_time = self.tracker.track_notification_received(task_id)
                print(f"✉️ Notification received for task {task_id} after {check_count} database checks: {delivery_time:.2f} ms")
                found = True
                break
            
            # Print status every 5 seconds to show progress
            elapsed = time.time() - start_time
            if int(elapsed) % 5 == 0 and int(elapsed) > 0:
                print(f"  Still waiting... {int(elapsed)}s elapsed, {check_count} database checks made")
            
            # Wait before checking again
            time.sleep(DB_CHECK_INTERVAL)
        
        if not found:
            print(f"⚠️ No notification found for task {task_id} after {MAX_WAIT_TIME} seconds ({check_count} database checks)")
            
        return found
    
    @task
    def test_notification_flow(self):
        """Run the end-to-end notification test"""
        try:
            # Stop if we've tested enough tasks
            if self.task_count >= TASK_COUNT:
                # Stop the test
                self.environment.runner.quit()
                return
            
            print(f"\n==== Starting test iteration {self.task_count + 1}/{TASK_COUNT} ====")
            
            # Create a task
            task_id = self.create_task()
            if not task_id:
                print("❌ Failed to create task, aborting this iteration")
                return
            
            # Assign the task (this triggers notification)
            success = self.assign_task(task_id)
            if not success:
                print("❌ Failed to assign task, aborting this iteration")
                return
            
            # Increment task count
            self.task_count += 1
            
        except Exception as e:
            print(f"❌ Error in test flow: {e}")
            import traceback
            traceback.print_exc()

# =====================================================================
# Main entry point for direct execution
# =====================================================================

def run_standalone_test(implementation, host):
    """Run test without Locust UI"""
    from locust.env import Environment
    from locust.stats import stats_printer, stats_history
    import gevent
    
    # Configure environment
    env = Environment(user_classes=[NotificationTestUser])
    env.implementation = implementation
    env.host = host
    
    # Start environment
    env.create_local_runner()
    
    # Set up logging
    gevent.spawn(stats_printer(env.stats))
    
    # Start runner with 1 user
    env.runner.start(1, spawn_rate=1)
    
    # Run until complete
    start_time = time.time()
    tracker = None
    
    # Create a shared tracker for all users
    shared_tracker = PerformanceTracker(implementation)
    env.shared_tracker = shared_tracker
    
    try:
        print(f"Running {implementation} implementation test...")
        while True:
            # Reference the shared tracker
            tracker = env.shared_tracker
                
            # If all tasks completed or timeout
            if (tracker and len(tracker.notification_times) >= TASK_COUNT) or \
               time.time() - start_time > MAX_WAIT_TIME * (TASK_COUNT + 2):
                break
                
            gevent.sleep(1)
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        # Mark test as finished for throughput calculations
        if tracker:
            tracker.finish_test()
            
            # Generate report
            report_file = tracker.save_report()
            
            # Print summary
            report = tracker.get_report()
            print("\n----- Performance Summary -----")
            print(f"Implementation: {implementation}")
            print(f"Test duration: {report['test_duration']['formatted']}")
            print(f"Tasks tested: {report['metrics']['total_tasks']}")
            print(f"Notifications received: {report['metrics']['sample_count']}")
            print(f"Success rate: {report['metrics']['success_rate'] * 100:.1f}%")
            
            if tracker.notification_times:
                metrics = report["metrics"]["notification_times_ms"]
                print(f"\nLatency Metrics:")
                print(f"  Average delivery time: {metrics['average']:.2f} ms")
                print(f"  Median delivery time: {metrics['median']:.2f} ms")
                print(f"  90th percentile: {metrics['p90']:.2f} ms")
                print(f"  95th percentile: {metrics['p95']:.2f} ms")
                print(f"  99th percentile: {metrics['p99']:.2f} ms")
                print(f"  Maximum delivery time: {metrics['max']:.2f} ms")
                print(f"  Standard deviation: {metrics['std_dev']:.2f} ms")
                
                print(f"\nThroughput Metrics:")
                print(f"  Notifications per second: {report['throughput']['notifications_per_second']:.2f}")
                print(f"  Tasks per second: {report['throughput']['tasks_per_second']:.2f}")

                if 'task_creation_performance' in report and report['task_creation_performance']:
                    creation = report['task_creation_performance']
                    print(f"\nTask Creation Performance:")
                    print(f"  Average creation time: {creation['average_ms']:.2f} ms")
                    print(f"  Min creation time: {creation['min_ms']:.2f} ms")
                    print(f"  Max creation time: {creation['max_ms']:.2f} ms")

                if 'resource_usage' in report and report['resource_usage']['cpu']:
                    cpu = report['resource_usage']['cpu']
                    memory = report['resource_usage']['memory']
                    print(f"\nResource Usage:")
                    print(f"  Memory average: {memory.get('average_mb', 0):.1f} MB")
                    print(f"  Memory peak: {memory.get('peak_mb', 0):.1f} MB")
            
            print("------------------------------")
        
        # Stop runner
        env.runner.quit()

def print_comparison(rabbitmq_file, polling_file):
    """Print a comparison between RabbitMQ and polling implementations"""
    try:
        with open(rabbitmq_file, 'r') as f:
            rabbitmq_data = json.load(f)
        
        with open(polling_file, 'r') as f:
            polling_data = json.load(f)
        
        print("\n===== RabbitMQ vs Polling Implementation Performance Comparison =====")
        
        # Get metrics
        rmq_metrics = rabbitmq_data.get("metrics", {}).get("notification_times_ms", {})
        poll_metrics = polling_data.get("metrics", {}).get("notification_times_ms", {})
        
        rmq_throughput = rabbitmq_data.get("throughput", {}).get("notifications_per_second", 0)
        poll_throughput = polling_data.get("throughput", {}).get("notifications_per_second", 0)
        
        rmq_checks = rabbitmq_data.get("database_checks", {}).get("average_checks_per_notification", 0)
        poll_checks = polling_data.get("database_checks", {}).get("average_checks_per_notification", 0)
        
        # Print comparison table
        print("\nMetric                    | RabbitMQ        | Polling         | Difference")
        print("-------------------------|-----------------|-----------------|------------------")
        print(f"Average latency (ms)      | {rmq_metrics.get('average', 0):.2f}             | {poll_metrics.get('average', 0):.2f}             | {poll_metrics.get('average', 0) - rmq_metrics.get('average', 0):.2f}")
        print(f"95th percentile (ms)      | {rmq_metrics.get('p95', 0):.2f}             | {poll_metrics.get('p95', 0):.2f}             | {poll_metrics.get('p95', 0) - rmq_metrics.get('p95', 0):.2f}")
        print(f"99th percentile (ms)      | {rmq_metrics.get('p99', 0):.2f}             | {poll_metrics.get('p99', 0):.2f}             | {poll_metrics.get('p99', 0) - rmq_metrics.get('p99', 0):.2f}")
        print(f"Max latency (ms)          | {rmq_metrics.get('max', 0):.2f}             | {poll_metrics.get('max', 0):.2f}             | {poll_metrics.get('max', 0) - rmq_metrics.get('max', 0):.2f}")
        print(f"Throughput (notifs/sec)   | {rmq_throughput:.2f}             | {poll_throughput:.2f}             | {poll_throughput - rmq_throughput:.2f}")
        print(f"Avg DB checks per notif   | {rmq_checks:.2f}             | {poll_checks:.2f}             | {poll_checks - rmq_checks:.2f}")
        
        print("\n===== Conclusion =====")
        
        if rmq_metrics.get('average', 0) < poll_metrics.get('average', 0):
            latency_winner = "RabbitMQ"
            latency_factor = poll_metrics.get('average', 0) / rmq_metrics.get('average', 0) if rmq_metrics.get('average', 0) > 0 else 0
        else:
            latency_winner = "Polling"
            latency_factor = rmq_metrics.get('average', 0) / poll_metrics.get('average', 0) if poll_metrics.get('average', 0) > 0 else 0
        
        if rmq_throughput > poll_throughput:
            throughput_winner = "RabbitMQ"
            throughput_factor = rmq_throughput / poll_throughput if poll_throughput > 0 else 0
        else:
            throughput_winner = "Polling"
            throughput_factor = poll_throughput / rmq_throughput if rmq_throughput > 0 else 0
        
        print(f"- Latency: {latency_winner} implementation is faster by {latency_factor:.1f}x")
        print(f"- Throughput: {throughput_winner} implementation has higher throughput by {throughput_factor:.1f}x")
        
        if rmq_checks < poll_checks:
            check_efficiency = f"RabbitMQ implementation is more efficient, requiring {rmq_checks:.1f} DB checks vs {poll_checks:.1f} for polling implementation"
        else:
            check_efficiency = f"Polling implementation is more efficient, requiring {poll_checks:.1f} DB checks vs {rmq_checks:.1f} for RabbitMQ implementation"
        
        print(f"- Database efficiency: {check_efficiency}")
        
        print("\nRecommendation:")
        if latency_winner == "RabbitMQ" and throughput_winner == "RabbitMQ":
            print("RabbitMQ implementation outperforms polling implementation in both latency and throughput, making it the recommended choice.")
        elif latency_winner == "Polling" and throughput_winner == "Polling":
            print("Polling implementation outperforms RabbitMQ implementation in both latency and throughput, making it the recommended choice.")
        else:
            print(f"There's a tradeoff: {latency_winner} implementation has better latency, while {throughput_winner} implementation has better throughput.")
            print(f"Choose based on your priority (lower latency vs higher throughput).")
    
    except Exception as e:
        print(f"Error comparing reports: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run end-to-end notification performance test")
    parser.add_argument("--implementation", required=True, choices=["rabbitmq", "polling"],
                        help="Notification implementation to test (rabbitmq or polling)")
    parser.add_argument("--host", default="http://localhost:8000", 
                        help="API host to test against")
    parser.add_argument("--tasks", type=int, default=TASK_COUNT,
                        help="Number of tasks to test")
    parser.add_argument("--compare", action="store_true",
                        help="Compare rabbitmq and polling implementations after running tests")
    
    args = parser.parse_args()
    
    # Update task count
    TASK_COUNT = args.tasks
    
    # Run standalone test
    run_standalone_test(args.implementation, args.host)
    
    # If comparison requested, generate the other implementation's report too
    if args.compare:
        # Get most recent files for each implementation
        import glob
        
        rabbitmq_files = sorted(glob.glob("notification_perf_rabbitmq_*.json"), reverse=True)
        polling_files = sorted(glob.glob("notification_perf_polling_*.json"), reverse=True)
        
        # If missing a type, run that test
        if args.implementation == "rabbitmq" and not polling_files:
            print("\nRunning polling implementation test for comparison...")
            run_standalone_test("polling", args.host)
            polling_files = sorted(glob.glob("notification_perf_polling_*.json"), reverse=True)
        elif args.implementation == "polling" and not rabbitmq_files:
            print("\nRunning rabbitmq implementation test for comparison...")
            run_standalone_test("rabbitmq", args.host)
            rabbitmq_files = sorted(glob.glob("notification_perf_rabbitmq_*.json"), reverse=True)
        
        # Compare the most recent files
        if rabbitmq_files and polling_files:
            print_comparison(rabbitmq_files[0], polling_files[0])
        else:
            print("Missing test reports for comparison")