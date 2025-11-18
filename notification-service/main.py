import logging
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import Base, engine
from controllers.notification_controller import router as notification_router
from services.consumer import NotificationConsumer
from controllers.contest_controller import router as contest_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Create consumer instance
consumer = NotificationConsumer()
consumer_thread = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for FastAPI app - handles startup and shutdown events"""
    # Startup event - start consumer in a background thread
    global consumer_thread
    consumer_thread = threading.Thread(target=consumer.start, daemon=True)
    consumer_thread.start()
    logging.info("Notification consumer started")

    yield  # App runs here

    # Shutdown event - stop consumer thread
    consumer.stop()
    if consumer_thread and consumer_thread.is_alive():
        consumer_thread.join(timeout=5)
    logging.info("Notification consumer stopped")


# Create FastAPI app with lifespan manager
app = FastAPI(title="Notification Service", lifespan=lifespan)
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
app.include_router(notification_router)
app.include_router(contest_router)
# For direct execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
