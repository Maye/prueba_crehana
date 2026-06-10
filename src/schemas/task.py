from datetime import datetime

from pydantic import BaseModel

from src.entities.task import TaskPriority, TaskStatus


class TaskCreateRequest(BaseModel):
    title: str
    description: str | None = None
    priority: TaskPriority = TaskPriority.medium


class TaskUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: TaskPriority | None = None


class TaskStatusUpdateRequest(BaseModel):
    status: TaskStatus


class TaskAssignRequest(BaseModel):
    assignee_id: int


class TaskResponse(BaseModel):
    id: int
    task_list_id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListTasksResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int
    completion_percentage: float
    page: int
    size: int
    pages: int
