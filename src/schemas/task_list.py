from datetime import datetime

from pydantic import BaseModel


class TaskListCreateRequest(BaseModel):
    title: str
    description: str | None = None


class TaskListUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None


class TaskListResponse(BaseModel):
    id: int
    title: str
    description: str | None
    owner_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedTaskListResponse(BaseModel):
    items: list[TaskListResponse]
    total: int
    page: int
    size: int
    pages: int
