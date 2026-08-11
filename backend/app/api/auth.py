from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.core.deps import get_current_user
from app.schemas.user import UserCreate, UserLogin, UserRead, Token
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new student, faculty, staff, or admin user."""
    auth_service = AuthService(db)
    new_user = await auth_service.register_user(user_in)
    return new_user


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user credentials and receive JWT access & refresh tokens."""
    auth_service = AuthService(db)
    token = await auth_service.authenticate_user(credentials)
    return token


@router.get("/me", response_model=UserRead)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Retrieve details of currently authenticated user."""
    return current_user
