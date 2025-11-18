from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from typing import List, Optional

from models.tasks_assigned import Task, TaskStatus
from schemas.tasks_assigned_schema import (
    TaskStatus,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    TaskAssignRequest,
)

class TaskService:
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, task: TaskCreate):
        """Create a new task"""
        # Set default due date to 7 days from today if not provided
        due_date = task.due_date
        if not due_date:
            due_date = datetime.now().date() + timedelta(days=7)

        # Create new task
        db_task = Task(
            userid=task.userid,
            mentorid=task.mentorid,
            due_date=due_date,
            status=task.status,
            hasbeensubmittedbymentor=False,  # Default to False for new tasks
            problem_name=task.problem_name,
            difficulty=task.difficulty,
            difficulty_category=task.difficulty_category,
            tags=task.tags,
            matched_recommendation=task.matched_recommendation,
            contestid=task.contestid,
            index=task.index,
        )

        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)

        return db_task

    def get_task_by_id(self, task_id: int, user_id: int, is_mentor: bool):
        """Get a task by ID with permission check"""
        task = self.db.query(Task).filter(Task.id == task_id).first()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        # If user is learner and task is not submitted by mentor yet, deny access
        if not is_mentor and task.userid == user_id and not task.hasbeensubmittedbymentor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This task has not been assigned to you yet",
            )

        # Otherwise check general permission
        if task.userid != user_id and task.mentorid != user_id and not is_mentor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )

        return task

    def get_tasks_by_user_id(
        self, user_id: int, current_user_id: int, is_mentor: bool, task_status: Optional[TaskStatus] = None
    ):
        """Get tasks for a specific user with permission check"""
        if current_user_id != user_id and not is_mentor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )

        query = self.db.query(Task).filter(Task.userid == user_id)

        # For learners, only show tasks that have been submitted by mentor
        if not is_mentor and current_user_id == user_id:
            query = query.filter(Task.hasbeensubmittedbymentor == True)

        if task_status:
            query = query.filter(Task.status == task_status)

        tasks = query.all()

        return tasks

    def get_tasks_by_mentor_id(self, mentor_id: int, user_id: int, role: str):
        """Get tasks assigned by a specific mentor with permission check"""
        # Only the mentor themselves or mentors can see all assigned tasks
        if user_id != mentor_id and role != "mentor":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )

        tasks = self.db.query(Task).filter(Task.mentorid == mentor_id).all()

        return tasks

    def assign_tasks(self, task_assignments: List[TaskAssignRequest], mentor_id: int):
        """Assign tasks to learners with permission check"""
        updated_tasks = []

        for assignment in task_assignments:
            # Get the task
            task = self.db.query(Task).filter(Task.id == assignment.task_id).first()

            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with ID {assignment.task_id} not found",
                )

            # Verify that this mentor created the task
            if task.mentorid != mentor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
                )

            # Update the task
            task.hasbeensubmittedbymentor = True
            task.due_date = assignment.due_date

            self.db.commit()
            self.db.refresh(task)

            updated_tasks.append(task)

        return updated_tasks

    def update_task(self, task_id: int, task_update: TaskUpdate, user_id: int, role: str):
        """Update a task with permission check"""
        # Get the existing task
        db_task = self.db.query(Task).filter(Task.id == task_id).first()

        if not db_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        # Check if user has permission to update
        is_mentor = role == "mentor"
        is_task_user = db_task.userid == user_id
        is_task_mentor = db_task.mentorid == user_id

        if not is_mentor and not is_task_user and not is_task_mentor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )

        # If user is not a mentor, they can only update status
        if not is_mentor and not is_task_mentor:
            # Reset all fields except status
            task_update_dict = {"status": task_update.status}
        else:
            task_update_dict = task_update.dict(exclude_unset=True)

        # Update task fields
        for key, value in task_update_dict.items():
            if value is not None:
                setattr(db_task, key, value)

        # Auto-update status based on due date
        if (
            db_task.status == TaskStatus.pending
            and db_task.due_date < datetime.now().date()
        ):
            db_task.status = TaskStatus.overdue

        self.db.commit()
        self.db.refresh(db_task)

        return db_task

    def delete_task(self, task_id: int, mentor_id: int):
        """Delete a task with permission check"""
        # Get the task
        db_task = self.db.query(Task).filter(Task.id == task_id).first()

        if not db_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        # Verify that this mentor created the task
        if db_task.mentorid != mentor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )

        # Delete the task
        self.db.delete(db_task)
        self.db.commit()