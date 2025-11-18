from fastapi import FastAPI
from api.routes import router as api_router
from core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from database.connection import engine, Base
import uvicorn
import logging

app = FastAPI(
    title="AI Recommendation and Summary Service",
    description="Microservice for generating AI-powered programming recommendations and summaries",
    version="1.0.0",
)

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


app.include_router(api_router, prefix=settings.API_PREFIX)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("ai_service.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)
logger.info("Tables registered with SQLAlchemy: %s", Base.metadata.tables.keys())


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


# Run the application with uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
