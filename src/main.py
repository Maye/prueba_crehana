from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.config.settings import settings
from src.exceptions.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    TaskListNotFoundError,
    TaskNotFoundError,
    UserNotFoundError,
)
from src.routers.auth import router as auth_router
from src.routers.task import router as task_router
from src.routers.task_list import router as task_list_router

app = FastAPI(
    title=settings.app_name,
    description="API REST para gestión de listas de tareas",
    version="0.1.0",
)


@app.exception_handler(TaskListNotFoundError)
async def task_list_not_found_handler(request: Request, exc: TaskListNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(request: Request, exc: TaskNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(EmailAlreadyExistsError)
async def email_exists_handler(request: Request, exc: EmailAlreadyExistsError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


app.include_router(auth_router)
app.include_router(task_list_router)
app.include_router(task_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok"}
