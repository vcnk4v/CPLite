from fastapi import FastAPI, HTTPException, BackgroundTasks, Response
import asyncio
import os
import logging
from datetime import datetime
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("recommendation_service_api.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("recommendation_api")

# Import the main processing function
from main import process_all_users

# Create FastAPI app
app = FastAPI(title="Recommendation Service API")

# Track if a job is currently running
job_status = {
    "is_running": False,
    "last_start": None,
    "last_end": None,
    "last_status": None,
}

# Lock file path for tracking job status across restarts
LOCK_FILE = "/app/job_lock.json"

# Load job status from file on startup if it exists
try:
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE, "r") as f:
            stored_status = json.load(f)
            job_status.update(stored_status)
            logger.info(f"Loaded job status from file: {job_status}")
except Exception as e:
    logger.error(f"Error loading job status: {e}")

def save_job_status():
    """Save job status to file"""
    try:
        with open(LOCK_FILE, "w") as f:
            json.dump(job_status, f)
    except Exception as e:
        logger.error(f"Error saving job status: {e}")

async def run_recommendation_job():
    """Run the recommendation job with proper status tracking"""
    global job_status
    
    if job_status["is_running"]:
        logger.info("Job already running, skipping")
        return
    
    try:
        # Update job status
        job_status["is_running"] = True
        job_status["last_start"] = datetime.now().isoformat()
        save_job_status()
        
        # Run the actual job
        logger.info("Starting recommendation processing job")
        await process_all_users()
        
        # Update job status on success
        job_status["last_status"] = "success"
        logger.info("Recommendation job completed successfully")
        
    except Exception as e:
        # Update job status on error
        job_status["last_status"] = f"error: {str(e)}"
        logger.error(f"Error in recommendation job: {e}")
        
    finally:
        # Always mark the job as completed
        job_status["is_running"] = False
        job_status["last_end"] = datetime.now().isoformat()
        save_job_status()

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok", "service": "recommendation-service"}

@app.get("/status")
async def get_job_status():
    """Get the current status of the recommendation job"""
    return job_status

@app.post("/run")
async def run_job(background_tasks: BackgroundTasks):
    """
    Trigger the recommendation job
    
    If the job is already running, returns 409 Conflict
    Otherwise, starts the job in the background and returns 202 Accepted
    """
    if job_status["is_running"]:
        # If already running, return conflict
        return Response(
            content=json.dumps({
                "status": "conflict",
                "message": "Job already running",
                "started_at": job_status["last_start"]
            }),
            status_code=409,
            media_type="application/json"
        )
    
    # Start job in background
    background_tasks.add_task(run_recommendation_job)
    
    return Response(
        content=json.dumps({
            "status": "accepted",
            "message": "Job started in background"
        }),
        status_code=202,
        media_type="application/json"
    )

@app.post("/run-sync")
async def run_job_sync():
    """
    Trigger the recommendation job and wait for completion
    
    If the job is already running, returns 409 Conflict
    Otherwise, runs the job and returns 200 OK when complete
    """
    if job_status["is_running"]:
        # If already running, return conflict
        return Response(
            content=json.dumps({
                "status": "conflict",
                "message": "Job already running",
                "started_at": job_status["last_start"]
            }),
            status_code=409,
            media_type="application/json"
        )
    
    # Run the job synchronously
    await run_recommendation_job()
    
    return {
        "status": "completed",
        "last_start": job_status["last_start"],
        "last_end": job_status["last_end"],
        "result": job_status["last_status"]
    }