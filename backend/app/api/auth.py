from datetime import datetime, timedelta

from authlib.common.security import generate_token
from fastapi import APIRouter, Depends, Form, Request, HTTPException
from sqlmodel import Session, select

from app.core.security import get_session_user, verify_password, get_password_hash
from app.db.session import get_db
from app.models.auth import BrowserSession
from app.models.user import User
from app.schemas.user import UserRead

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

@router.post('', operation_id="auth_session_login")
async def auth_login(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        session: Session = Depends(get_db)
):
    """
    Login and create a database-backed session for OAuth2 authorization.
    """
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(password, user.hashed_password):
        # Also try by email
        user = session.exec(select(User).where(User.email == username)).first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create a new BrowserSession
    session_id = generate_token(32)
    session_secret = generate_token(64)
    session_secret_hash = get_password_hash(session_secret)
    
    # Session expires in 30 days
    expires_at = datetime.utcnow() + timedelta(days=30)
    
    db_session = BrowserSession(
        session_id=session_id,
        session_secret_hash=session_secret_hash,
        user_id=user.id,
        expires_at=expires_at
    )
    
    session.add(db_session)
    session.commit()
    
    # Store in cookie-based session (encrypted by SessionMiddleware)
    request.session['session_id'] = session_id
    request.session['session_secret'] = session_secret
    
    return {"message": "Logged in successfully"}


@router.post('/logout', operation_id="auth_session_logout")
async def auth_logout(
        request: Request,
        session: Session = Depends(get_db)
):
    """
    Logout and revoke the current browser session.
    """
    session_id = request.session.get("session_id")
    if session_id:
        db_session = session.exec(
            select(BrowserSession).where(BrowserSession.session_id == session_id)
        ).first()
        if db_session:
            db_session.revoked_at = datetime.utcnow()
            session.add(db_session)
            session.commit()
    
    # Clear session cookie
    request.session.clear()
    return {"message": "Logged out successfully"}


@router.get('/me', response_model=UserRead, operation_id="auth_session_me")
async def auth_session_me(current_user: User = Depends(get_session_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not logged in")
    return current_user
