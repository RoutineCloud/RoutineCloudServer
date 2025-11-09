from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import UserRead

# Create router
router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.get("/me", response_model=UserRead, operation_id="users_me")
async def get_current_user(
        current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    """
    return UserRead(username=current_user.username,
                    email=current_user.email,
                    is_active=current_user.is_active
                    )
