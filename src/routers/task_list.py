from fastapi import APIRouter, Depends, Query

from src.controllers.task_list import TaskListController
from src.schemas.task_list import (
    PaginatedTaskListResponse,
    TaskListCreateRequest,
    TaskListResponse,
    TaskListUpdateRequest,
)

router = APIRouter(prefix="/task-lists", tags=["task-lists"])


@router.get("/", response_model=PaginatedTaskListResponse)
async def list_task_lists(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    controller: TaskListController = Depends(),
):
    return await controller.list_all(page=page, size=size)


@router.post("/", response_model=TaskListResponse, status_code=201)
async def create_task_list(
    data: TaskListCreateRequest, controller: TaskListController = Depends()
):
    return await controller.create(data)


@router.get("/{task_list_id}", response_model=TaskListResponse)
async def get_task_list(task_list_id: int, controller: TaskListController = Depends()):
    return await controller.get_one(task_list_id)


@router.put("/{task_list_id}", response_model=TaskListResponse)
async def update_task_list(
    task_list_id: int,
    data: TaskListUpdateRequest,
    controller: TaskListController = Depends(),
):
    return await controller.update(task_list_id, data)


@router.delete("/{task_list_id}", status_code=204)
async def delete_task_list(
    task_list_id: int, controller: TaskListController = Depends()
):
    await controller.delete(task_list_id)
