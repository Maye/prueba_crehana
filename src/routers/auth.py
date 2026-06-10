from fastapi import APIRouter, Depends

from src.controllers.auth import AuthController
from src.schemas.user import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: UserRegisterRequest,
    controller: AuthController = Depends(),
):
    return await controller.register(data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLoginRequest,
    controller: AuthController = Depends(),
):
    return await controller.login(data)
