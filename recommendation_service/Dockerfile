FROM python:alpine

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends gcc \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a file to store job status that persists across container restarts
RUN touch /app/job_lock.json && chmod 666 /app/job_lock.json

# Default command starts the API server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]