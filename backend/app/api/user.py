from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.security import get_current_user, get_current_active_superuser, oauth2_scheme, sync_user_with_oidc
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
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db),
        token: str = Depends(oauth2_scheme)
):
    """
    Get current user information and sync with OIDC
    """
    sync_user_with_oidc(session, current_user, token)
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
