from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.security import get_current_user, verify_password, get_password_hash, get_current_active_superuser
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserRead, UserPasswordUpdate, UserCreate

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
                    is_active=current_user.is_active,
                    is_superuser=current_user.is_superuser
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

@router.post("/", response_model=UserRead, operation_id="users_create")
async def create_user(
    *,
    session: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Create new user.
    """
    user = session.exec(select(User).where(User.email == user_in.email)).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = session.exec(select(User).where(User.username == user_in.username)).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    
    db_obj = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj

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
