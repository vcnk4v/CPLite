#!/bin/bash

# Configuration
MAX_RETRIES=3
RETRY_DELAY=60  # seconds
RECOMMENDATION_SERVICE_URL="http://recommendation-service:8000"
LOG_FILE="/var/log/cron/recommendation_job.log"

# Create log directory if it doesn't exist
mkdir -p $(dirname $LOG_FILE)

# Function to log messages
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

log "Starting recommendation job..."

# First, check if job is already running
status_response=$(curl -s -o /tmp/status_response.json -w "%{http_code}" ${RECOMMENDATION_SERVICE_URL}/status)
status_code=$?

if [ $status_code -ne 0 ]; then
  log "Error: Failed to connect to recommendation service (curl exit code: $status_code)"
  exit 1
fi

if [ "$status_response" != "200" ]; then
  log "Error: Status endpoint returned non-200 status code: $status_response"
  cat /tmp/status_response.json | tee -a $LOG_FILE
  exit 1
fi

# Parse the JSON response to check if job is running
is_running=$(cat /tmp/status_response.json | grep -o '"is_running": true' | wc -l)

if [ $is_running -gt 0 ]; then
  log "Job is already running, exiting"
  exit 0
fi

# Job is not running, try to start it
retry_count=0

while [ $retry_count -lt $MAX_RETRIES ]; do
  log "Attempt $(($retry_count + 1))/$MAX_RETRIES: Starting recommendation job..."
  
  # Make the POST request to start the job synchronously
  response=$(curl -s -o /tmp/run_response.json -w "%{http_code}" -X POST ${RECOMMENDATION_SERVICE_URL}/run-sync)
  curl_status=$?
  
  # Check if the curl command succeeded
  if [ $curl_status -ne 0 ]; then
    log "Error: Failed to connect to recommendation service (curl exit code: $curl_status)"
    retry_count=$((retry_count + 1))
    
    if [ $retry_count -lt $MAX_RETRIES ]; then
      log "Retrying in $RETRY_DELAY seconds..."
      sleep $RETRY_DELAY
      continue
    else
      log "Max retries reached, exiting with failure"
      exit 1
    fi
  fi
  
  # Check the HTTP status code
  if [ "$response" = "200" ]; then
    log "Job completed successfully"
    cat /tmp/run_response.json | tee -a $LOG_FILE
    exit 0
  elif [ "$response" = "409" ]; then
    log "Job is already running (conflict)"
    cat /tmp/run_response.json | tee -a $LOG_FILE
    exit 0
  else
    log "Error: Unexpected status code: $response"
    cat /tmp/run_response.json | tee -a $LOG_FILE
    
    retry_count=$((retry_count + 1))
    if [ $retry_count -lt $MAX_RETRIES ]; then
      log "Retrying in $RETRY_DELAY seconds..."
      sleep $RETRY_DELAY
      continue
    else
      log "Max retries reached, exiting with failure"
      exit 1
    fi
  fi
done

log "Failed to run job after $MAX_RETRIES attempts"
exit 1