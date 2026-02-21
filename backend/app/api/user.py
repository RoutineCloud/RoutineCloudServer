from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.security import get_current_user, verify_password, get_password_hash
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserRead, UserPasswordUpdate

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
    return UserRead(username=current_user.username,
                    email=current_user.email,
                    is_active=current_user.is_active
                    )

@router.post("/change-password", operation_id="users_change_password")
async def change_password(
    password_data: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Change current user's password
    """
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    session.add(current_user)
    session.commit()
    
    return {"message": "Password changed successfully"}
