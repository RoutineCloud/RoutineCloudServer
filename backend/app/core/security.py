from typing import Annotated
from typing import Optional, Union

from authlib.jose import JoseError, JsonWebToken
from fastapi import Depends, HTTPException, status
from fastapi import Form
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class OAuth2DeviceCodeForm:
    def __init__(
            self,
            *,
            client_id: Annotated[str, Form()] = None,
            scope: Annotated[str, Form()] = "",
            device_uuid: Annotated[Optional[str], Form()] = None,
    ):
        self.client_id = client_id
        self.scope = scope
        # optional unique device identifier provided by the device
        self.device_uuid = (device_uuid or "").strip() if device_uuid else None

class OAuthAuthorizeForm:
    def __init__(
        self,
        *,
        response_type: Annotated[Optional[str], Form()] = None,
        client_id: Annotated[Optional[str], Form()] = None,
        redirect_uri: Annotated[Optional[str], Form()] = None,
        state: Annotated[Optional[str], Form()] = "",
        scope: Annotated[str, Form()] = "",
        code_challenge: Annotated[Optional[str], Form()] = None,
        code_challenge_method: Annotated[str, Form()] = "S256",
        client_secret: Annotated[Optional[str], Form()] = None,
    ) -> None:
        self.response_type = response_type
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.state = state or ""
        self.scope = scope or ""
        self.code_challenge = code_challenge
        self.code_challenge_method = code_challenge_method or "S256"
        self.client_secret = client_secret

class DeviceVerifyForm:
    def __init__(
        self,
        *,
        user_code: Annotated[Optional[str], Form()] = None,
        name: Annotated[Optional[str], Form()] = None,
        approve: Annotated[Optional[bool], Form()] = True,
    ) -> None:
        self.user_code = (user_code or "").strip() if user_code else None
        self.name = name
        self.approve = True if approve is None else approve

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
        # device_code grant
        device_code: Annotated[Union[str, None], Form()] = None,
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
        self.device_code = device_code
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
        elif self.grant_type == "urn:ietf:params:oauth:grant-type:device_code":
            missing = []
            if not self.device_code:
                missing.append("device_code")
        elif self.grant_type == "refresh_token":
            if not self.refresh_token:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail="Missing required field for refresh_token grant: refresh_token")

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
    jwt = JsonWebToken([settings.OAUTH2_JWT_ALG])
    try:
        #TODO check if adding claims_options is good
        # Check if validate should be called
        claims = jwt.decode(token, settings.OAUTH2_JWT_KEY)
        sub = claims.get("sub")
        if not sub:
            raise credentials_exception
    except JoseError:
        raise credentials_exception

    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise credentials_exception

    user = session.exec(select(User).where(User.id == user_id)).first()

    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user