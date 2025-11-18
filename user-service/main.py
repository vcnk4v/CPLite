from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine

# from views import auth_views, user_views, learner_mentor_view, service_token_views
from controllers import (
    auth_controller,
    user_controller,
    learner_mentor_controller,
    service_token_controller,
)
import config

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="CPLite User Service",
    description="User authentication and profile management for CPLite",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # For production, use specific origins like ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth_controller.router)
app.include_router(user_controller.router)
app.include_router(learner_mentor_controller.router)
app.include_router(service_token_controller.router)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "environment": config.ENVIRONMENT}


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
