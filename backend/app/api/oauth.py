import base64
import hashlib
import secrets
import jwt
from datetime import timedelta, datetime
from typing import Dict, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import or_
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import create_access_token, get_current_user, verify_password, OAuth2TokenForm, ALGORITHM
from app.db.session import get_db
from app.models.user import User
from app.schemas.security import Token

ACCESS_TOKEN_EXPIRE_MINUTES = 30

# In-memory stores (minimal change, no migrations)
AUTH_CODES: Dict[str, Dict] = {}
USER_SECRETS: Dict[int, str] = {}

# Create router
router = APIRouter(
    prefix="/api/oauth",
    tags=["authentication"],
    responses={401: {"description": "Unauthorized"}},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/oauth/token")


def _validate_redirect_uri(redirect_uri: str) -> None:
    allowed = [str(u) for u in settings.OAUTH_ALLOWED_REDIRECT_URIS or []]
    if redirect_uri not in allowed:
        raise HTTPException(status_code=400, detail="invalid_redirect_uri")


def _parse_basic_auth(authorization: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not authorization or not authorization.startswith("Basic "):
        return None, None
    try:
        decoded = base64.b64decode(authorization.split(" ", 1)[1]).decode("utf-8")
        cid, csec = decoded.split(":", 1)
        return cid, csec
    except Exception:
        return None, None


def _validate_client(client_id: Optional[str], client_secret: Optional[str]) -> None:
    # If a secret is configured, require it; otherwise treat client as public
    configured_secret = settings.OAUTH_CLIENT_SECRET
    if configured_secret:
        if client_id != settings.OAUTH_CLIENT_ID or client_secret != configured_secret:
            raise HTTPException(status_code=401, detail="invalid_client_credentials")


def _verify_pkce(code_verifier: Optional[str], code_challenge: str, method: str) -> bool:
    if method.upper() == "S256":
        if not code_verifier:
            return False
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        return computed == code_challenge
    elif method.lower() == "plain":
        return (code_verifier or "") == code_challenge
    else:
        # Unsupported method
        return False


@router.post("/token")
async def login_for_access_token(
    request: Request,
    token_form: OAuth2TokenForm = Depends(OAuth2TokenForm),
    db: Session = Depends(get_db),
):
    """
    OAuth2 Token Endpoint
    - Supports Password Grant (username/password)
    - Supports Authorization Code Grant with PKCE (Alexa/public client)
    """
    if token_form.grant_type == "password":
        user = db.exec(
            select(User).where(or_(User.username == token_form.username, User.email == token_form.username))
        ).first()
        if not user or not verify_password(token_form.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.username,
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "id": user.id,
                    "is_superuser": user.is_superuser,
                },
            },
            expires_delta=access_token_expires,
        )
        return Token(access_token=access_token, token_type="bearer")

    elif token_form.grant_type == "authorization_code":
        code = token_form.code
        redirect_uri = token_form.redirect_uri
        client_id = token_form.client_id
        code_verifier = token_form.code_verifier
        # Client Authentication: Basic header or form client_secret
        auth_header = request.headers.get("Authorization")
        basic_client_id, basic_client_secret = _parse_basic_auth(auth_header)

        #TODO check client_secret
        if basic_client_id and not client_id:
            client_id = basic_client_id

        _validate_client(client_id, basic_client_secret)

        if not code or not redirect_uri or not client_id:
            raise HTTPException(status_code=400, detail="invalid_request")

        record = AUTH_CODES.get(code)
        if not record:
            raise HTTPException(status_code=400, detail="invalid_grant")
        if record["exp"] < datetime.utcnow():
            # Expired; remove and error
            AUTH_CODES.pop(code, None)
            raise HTTPException(status_code=400, detail="expired_code")
        if record["client_id"] != client_id or record["redirect_uri"] != redirect_uri:
            raise HTTPException(status_code=400, detail="invalid_grant")

        # Verify PKCE
        if not _verify_pkce(code_verifier, record["code_challenge"], record["method"]):
            raise HTTPException(status_code=400, detail="invalid_pkce")

        # Consume code
        AUTH_CODES.pop(code, None)

        # Mint token for the user, include saved user_secret
        user = db.get(User, record["user_id"])
        if not user:
            raise HTTPException(status_code=400, detail="invalid_user")
        user_secret = USER_SECRETS.get(user.id) or record.get("user_secret")

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.username,
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "id": user.id,
                    "is_superuser": user.is_superuser,
                },
                "user_secret": user_secret,
                "client_id": client_id,
                "scope": record.get("scope", ""),
            },
            expires_delta=access_token_expires,
        )
        return Token(access_token=access_token, token_type="bearer")

    elif token_form.grant_type == "refresh_token":
        refresh_token = token_form.refresh_token
        try:
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"verify_exp": False},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=400, detail="invalid_grant")

        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=400, detail="invalid_grant")

        user = db.exec(
            select(User).where(or_(User.username == username, User.email == username))
        ).first()
        if not user:
            raise HTTPException(status_code=400, detail="invalid_grant")

        # Reuse optional claims if present
        client_id = payload.get("client_id")
        scope = payload.get("scope", "")
        user_secret = payload.get("user_secret") or USER_SECRETS.get(user.id)

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.username,
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "id": user.id,
                    "is_superuser": user.is_superuser,
                },
                "user_secret": user_secret,
                "client_id": client_id,
                "scope": scope,
            },
            expires_delta=access_token_expires,
        )
        return Token(access_token=access_token, token_type="bearer")
    else:
        raise HTTPException(status_code=400, detail="unsupported_grant_type")


@router.get("/auth")
async def authorize(
    response_type: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    scope: str = "",
    code_challenge: Optional[str] = None,
    code_challenge_method: str = "S256",
    client_secret: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    if response_type != "code":
        raise HTTPException(status_code=400, detail="unsupported_response_type")
    if not code_challenge:
        raise HTTPException(status_code=400, detail="Missing code_challenge (PKCE required)")

    _validate_redirect_uri(redirect_uri)
    _validate_client(client_id, client_secret)

    # Generate code and per-user secret
    code = secrets.token_urlsafe(32)
    user_secret = secrets.token_urlsafe(32)
    USER_SECRETS[current_user.id] = user_secret

    AUTH_CODES[code] = {
        "user_id": current_user.id,
        "scope": scope or "",
        "state": state or "",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "method": code_challenge_method or "S256",
        "user_secret": user_secret,
        "exp": datetime.utcnow() + timedelta(minutes=10),
    }

    return RedirectResponse(url=f"{redirect_uri}?code={code}&state={state}", status_code=302)


@router.get("/auth-json")
async def authorizeJson(
    response_type: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    scope: str = "",
    code_challenge: Optional[str] = None,
    code_challenge_method: str = "S256",
    client_secret: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    if response_type != "code":
        raise HTTPException(status_code=400, detail="unsupported_response_type")
    if not code_challenge:
        raise HTTPException(status_code=400, detail="Missing code_challenge (PKCE required)")

    _validate_redirect_uri(redirect_uri)
    _validate_client(client_id, client_secret)

    code = secrets.token_urlsafe(32)
    user_secret = secrets.token_urlsafe(32)
    USER_SECRETS[current_user.id] = user_secret

    AUTH_CODES[code] = {
        "user_id": current_user.id,
        "scope": scope or "",
        "state": state or "",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "method": code_challenge_method or "S256",
        "user_secret": user_secret,
        "exp": datetime.utcnow() + timedelta(minutes=10),
    }

    return {"redirect_to": f"{redirect_uri}?code={code}&state={state}"}