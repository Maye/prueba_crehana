from fastapi import APIRouter, Depends, Query

from src.controllers.task import TaskController
from src.schemas.task import (
    TaskAssignRequest,
    TaskCreateRequest,
    TaskListTasksResponse,
    TaskResponse,
    TaskStatusUpdateRequest,
    TaskUpdateRequest,
)

router = APIRouter(prefix="/task-lists/{task_list_id}/tasks", tags=["tasks"])


@router.get("/", response_model=TaskListTasksResponse)
async def list_tasks(
    task_list_id: int,
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    controller: TaskController = Depends(),
):
    return await controller.list_tasks(task_list_id, status, priority, page=page, size=size)


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task_list_id: int, data: TaskCreateRequest, controller: TaskController = Depends()
):
    return await controller.create(task_list_id, data)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_list_id: int, task_id: int, controller: TaskController = Depends()
):
    return await controller.get_one(task_id)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_list_id: int,
    task_id: int,
    data: TaskUpdateRequest,
    controller: TaskController = Depends(),
):
    return await controller.update(task_id, data)


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_list_id: int, task_id: int, controller: TaskController = Depends()
):
    await controller.delete(task_id)


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def change_task_status(
    task_list_id: int,
    task_id: int,
    data: TaskStatusUpdateRequest,
    controller: TaskController = Depends(),
):
    return await controller.change_status(task_id, data)


@router.patch("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_list_id: int,
    task_id: int,
    data: TaskAssignRequest,
    controller: TaskController = Depends(),
):
    return await controller.assign(task_id, data)


@router.post("/{task_id}/notify")
async def notify_task(
    task_list_id: int, task_id: int, controller: TaskController = Depends()
):
    return await controller.notify(task_id)
