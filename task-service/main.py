from fastapi import FastAPI
from controllers import tasks_assigned_controller
from fastapi.middleware.cors import CORSMiddleware
from db.database import engine, Base
import logging
import uvicorn

app = FastAPI(
    title="CPLite Task Service",
    description="CRUD operations of assigned_tasks database for CPLite",

)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, use specific origins like ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


app.include_router(tasks_assigned_controller.router)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("task_service.log"),
        logging.StreamHandler()
    ]
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
