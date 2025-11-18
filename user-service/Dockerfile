# Use Python 3.9 slim image
FROM python:alpine

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends gcc libpq-dev \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*
# RUN apk add --no-cache gcc musl-dev postgresql-dev

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port for the application
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
