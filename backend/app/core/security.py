from datetime import datetime, timedelta
from typing import Annotated
from typing import Any, Optional, Dict, Union

import jwt
from fastapi import Depends, HTTPException, status
from fastapi import Form
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.security import TokenData

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# JWT token settings
ALGORITHM = "HS256"



class OAuth2TokenForm:
    def __init__(
        self,
        *,
        # common
        grant_type: Annotated[Union[str, None], Form()] = None,
        scope: Annotated[str, Form()] = "",
        client_id: Annotated[Union[str, None], Form()] = None,
        client_secret: Annotated[Union[str, None], Form()] = None,
        # password grant
        username: Annotated[Union[str, None], Form(alias="username")] = None,
        password: Annotated[Union[str, None], Form(alias="password")] = None,
        # authorization_code grant
        code: Annotated[Union[str, None], Form()] = None,
        redirect_uri: Annotated[Union[str, None], Form()] = None,
        code_verifier: Annotated[Union[str, None], Form()] = None,
        # refresh_token grant
        refresh_token: Annotated[Union[str, None], Form()] = None,
    ) -> None:
        # assign all
        self.grant_type = grant_type
        self.scope = scope
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.code = code
        self.redirect_uri = redirect_uri
        self.code_verifier = code_verifier
        self.refresh_token = refresh_token

        # conditional validation to simulate specific forms' required fields
        # Raise 422 when required parameters for the selected grant are missing
        if not self.grant_type:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Missing required field: grant_type")
        if self.grant_type == "password":
            missing = []
            if not self.username:
                missing.append("username")
            if not self.password:
                missing.append("password")
            if missing:
                # FastAPI normally returns 422 for validation errors
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail=f"Missing required fields for password grant: {', '.join(missing)}")
        elif self.grant_type == "authorization_code":
            # client_id may come from Authorization header; don't enforce it here
            missing = []
            if not self.code:
                missing.append("code")
            if not self.redirect_uri:
                missing.append("redirect_uri")
            if missing:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail=f"Missing required fields for authorization_code grant: {', '.join(missing)}")
        elif self.grant_type == "refresh_token":
            if not self.refresh_token:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail="Missing required field for refresh_token grant: refresh_token")

def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password
    """
    return pwd_context.hash(password)

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                           session: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.InvalidTokenError:
        raise credentials_exception
    user = session.exec(select(User).where(User.username == token_data.username)).first()

    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user