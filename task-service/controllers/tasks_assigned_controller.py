from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import SessionLocal
from datetime import datetime, timedelta
from typing import List, Optional

from utils.auth_middleware_service import (
    require_authenticated,
    require_mentor,
)
from models.tasks_assigned import Task, TaskStatus
from schemas.tasks_assigned_schema import (
    TaskStatus,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    TaskAssignRequest,
)
from services.task_service import TaskService
from utils.messaging import RabbitMQClient

router = APIRouter(tags=["Assigned Tasks"])


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependency to get task service
def get_task_service(db: Session = Depends(get_db)):
    return TaskService(db)


# Routes
@router.post("/tasks/", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    auth_info=Depends(require_mentor),
    task_service: TaskService = Depends(get_task_service)
):
    """Create a new task (mentor only)"""
    return task_service.create_task(task)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    auth_info=Depends(require_authenticated),
    task_service: TaskService = Depends(get_task_service),
):
    """Get a task by ID"""
    user_id = int(auth_info["user_id"])
    is_mentor = auth_info["role"] == "mentor"

    return task_service.get_task_by_id(task_id, user_id, is_mentor)


@router.get("/tasks/user/{user_id}", response_model=List[TaskResponse])
async def get_user_tasks(
    user_id: int,
    task_status: Optional[TaskStatus] = None,
    auth_info=Depends(require_authenticated),
    task_service: TaskService = Depends(get_task_service),
):
    """Get tasks for a specific user"""
    current_user_id = int(auth_info["user_id"])
    is_mentor = auth_info["role"] == "mentor"
    print(f"Current user ID: {current_user_id}, User ID: {user_id}, Is mentor: {is_mentor}")

    return task_service.get_tasks_by_user_id(user_id, current_user_id, is_mentor, task_status)


@router.get("/tasks/mentor/{mentorid}", response_model=List[TaskResponse])
async def get_mentor_assigned_tasks(
    mentorid: int,
    auth_info=Depends(require_authenticated),
    task_service: TaskService = Depends(get_task_service),
):
    """Get tasks assigned by a specific mentor"""
    user_id = int(auth_info["user_id"])
    role = auth_info["role"]

    return task_service.get_tasks_by_mentor_id(mentorid, user_id, role)


@router.post("/tasks/assign", response_model=List[TaskResponse])
async def assign_tasks(
    task_assignments: List[TaskAssignRequest],
    auth_info=Depends(require_mentor),
    task_service: TaskService = Depends(get_task_service),
):
    """Assign tasks to learners (mentor only)"""
    mentor_id = int(auth_info["user_id"])

    try:
        updated_tasks = task_service.assign_tasks(task_assignments, mentor_id)

        # Prepare task events for notification
        task_events = [
            {
                "task_id": task.id,
                "mentor_id": task.mentorid,
                "user_id": task.userid,
                "title": task.problem_name,
                "due_date": task.due_date.isoformat() if task.due_date else None,
            }
            for task in updated_tasks
        ]

        # Publish batch notification
        if task_events:
            try:
                mq_client = RabbitMQClient()
                mq_client.setup_exchange("task_events")
                mq_client.publish(
                    exchange_name="task_events",
                    routing_key="task.batch_created",
                    message={"tasks": task_events},
                    message_type="tasks_batch_created",
                )
                mq_client.close()
            except Exception as e:
                # Log error but don't fail the request
                print(f"Error publishing batch message: {e}")

        return updated_tasks
    except HTTPException as e:
        raise e


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    auth_info=Depends(require_authenticated),
    task_service: TaskService = Depends(get_task_service),
):
    """Update a task"""
    user_id = int(auth_info["user_id"])
    role = auth_info["role"]

    return task_service.update_task(task_id, task_update, user_id, role)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    auth_info=Depends(require_mentor),
    task_service: TaskService = Depends(get_task_service)
):
    """Delete a task (mentor only)"""
    mentor_id = int(auth_info["user_id"])

    task_service.delete_task(task_id, mentor_id)
    return None