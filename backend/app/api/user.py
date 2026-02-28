from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.security import get_current_user, get_current_active_superuser
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserRead

# Create router
router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.get("/me", response_model=UserRead, operation_id="users_me")
async def get_current_user_me(
        current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    """
    return current_user

@router.get("/", response_model=list[UserRead], operation_id="users_list")
async def list_users(
    *,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """
    List all users.
    """
    users = session.exec(select(User)).all()
    return users
