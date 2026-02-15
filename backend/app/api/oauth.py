import base64
import hashlib
import secrets
import time
from datetime import timedelta
from typing import Dict, Optional, Tuple, Any

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import or_
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import create_access_token, get_current_user, verify_password, OAuth2TokenForm, ALGORITHM, \
    OAuth2DeviceCodeForm, OAuthAuthorizeForm, DeviceVerifyForm
from app.db.session import get_db
from app.models.device import Device, DeviceStatus
from app.models.oauth2 import DeviceCredential, OAuth2AuthorizationCode
from app.models.user import User
from app.schemas.security import Token, DeviceCodeResponse, AuthJsonResponse, DeviceVerificationResponse, DeviceInfo

ACCESS_TOKEN_EXPIRE_MINUTES = 30

# In-memory stores (minimal change, no migrations)
AUTH_CODES: Dict[str, Dict] = {}
USER_SECRETS: Dict[int, str] = {}
DEVICE_CODES: Dict[str, Dict] = {}

# Create router
router = APIRouter(
    prefix="/api/oauth_old",
    tags=["authentication"],
    responses={401: {"description": "Unauthorized"}},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/oauth/token")


def _validate_redirect_uri(redirect_uri: str) -> None:
    allowed = [str(u) for u in settings.OAUTH_ALLOWED_REDIRECT_URIS or []]
    if redirect_uri not in allowed:
        raise HTTPException(status_code=400, detail="invalid_redirect_uri")


def _parse_basic_auth(authorization: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    #TODO Check usage and why it is needed
    if not authorization or not authorization.startswith("Basic "):
        return None, None
    try:
        decoded = base64.b64decode(authorization.split(" ", 1)[1]).decode("utf-8")
        cid, csec = decoded.split(":", 1)
        return cid, csec
    except Exception:
        return None, None


def _validate_client(client_id: Optional[str], client_secret: Optional[str]) -> None:
    #TODO Update and check security

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

def _mint_access_token_for_user(user: User, *, extra_claims: Optional[Dict] = None,
                                expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    claims: Dict[str, Any] = {
        "sub": user.username,
        "user": {
            "username": user.username,
            "email": user.email,
            "id": user.id,
            "is_superuser": user.is_superuser,
        },
    }
    if extra_claims:
        claims.update(extra_claims)
    access_token_expires = timedelta(minutes=expires_minutes)
    return create_access_token(data=claims, expires_delta=access_token_expires)


def _handle_password_grant(token_form: OAuth2TokenForm, db: Session) -> Token:
    user = db.exec(
        select(User).where(or_(User.username == token_form.username, User.email == token_form.username))
    ).first()
    if not user or not verify_password(token_form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    jwt_token = _mint_access_token_for_user(user)
    return Token(access_token=jwt_token, token_type="bearer")


def _handle_auth_code_grant(request: Request, token_form: OAuth2TokenForm, db: Session) -> Token:
    code = token_form.code
    redirect_uri = token_form.redirect_uri
    client_id = token_form.client_id
    code_verifier = token_form.code_verifier
    # Client Authentication: Basic header or form client_secret
    auth_header = request.headers.get("Authorization")
    basic_client_id, basic_client_secret = _parse_basic_auth(auth_header)
    if basic_client_id and not client_id:
        client_id = basic_client_id
    _validate_client(client_id, basic_client_secret)
    if not code or not redirect_uri or not client_id:
        raise HTTPException(status_code=400, detail="invalid_request")
    # Load authorization code from DB
    ac = db.exec(select(OAuth2AuthorizationCode).where(OAuth2AuthorizationCode.code == code)).first()
    if not ac:
        raise HTTPException(status_code=400, detail="invalid_grant")
    # Expired?
    if ac.is_expired():
        db.delete(ac)
        db.commit()
        raise HTTPException(status_code=400, detail="expired_code")
    if ac.client_id != client_id or ac.redirect_uri != redirect_uri:
        raise HTTPException(status_code=400, detail="invalid_grant")
    if not _verify_pkce(code_verifier, ac.code_challenge or "", ac.code_challenge_method or "S256"):
        raise HTTPException(status_code=400, detail="invalid_pkce")
    # Consume code by deleting it
    user = db.get(User, ac.user_id)
    db.delete(ac)
    db.commit()
    if not user:
        raise HTTPException(status_code=400, detail="invalid_user")
    jwt_token = _mint_access_token_for_user(
        user,
        extra_claims={
            "client_id": client_id,
            "scope": ac.scope or "",
        },
    )
    return Token(access_token=jwt_token, token_type="bearer")


def _handle_device_code_grant(token_form: OAuth2TokenForm, db: Session) -> Token:
    device_code = token_form.device_code
    client_id = token_form.client_id
    # Read DeviceCredential from DB instead of in-memory dict
    cred = db.exec(select(DeviceCredential).where(DeviceCredential.device_code == device_code)).first()
    if not cred:
        raise HTTPException(status_code=400, detail={"error": "bad_verification_code"})
    # Expired?
    if cred.expires_at and cred.expires_at <= int(time.time()):
        cred.status = "expired"
        db.add(cred)
        db.commit()
        raise HTTPException(status_code=400, detail={"error": "expired_token"})
    if cred.client_id != client_id:
        raise HTTPException(status_code=400, detail={"error": "invalid_grant"})
    if cred.status == "pending":
        raise HTTPException(status_code=400, detail={"error": "authorization_pending"})
    if cred.status == "expired":
        raise HTTPException(status_code=400, detail={"error": "expired_token"})
    if cred.status == "denied":
        raise HTTPException(status_code=400, detail={"error": "authorization_declined"})
    if cred.status == "authorized":
        user = db.get(User, cred.user_id) if cred.user_id else None
        if not user:
            raise HTTPException(status_code=400, detail="invalid_user")
        jwt_token = _mint_access_token_for_user(
            user,
            extra_claims={
                "client_id": client_id,
                "scope": cred.scope or "",
            },
        )
        return Token(access_token=jwt_token, token_type="bearer")
    raise HTTPException(status_code=400, detail="invalid_grant")


def _handle_refresh_token_grant(token_form: OAuth2TokenForm, db: Session) -> Token:
    refresh_token = token_form.refresh_token
    try:
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM]
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
    jwt_token = _mint_access_token_for_user(
        user,
        extra_claims={
            "client_id": payload.get("client_id"),
            "scope": payload.get("scope", ""),
        },
    )
    return Token(access_token=jwt_token, token_type="bearer")


@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    token_form: OAuth2TokenForm = Depends(OAuth2TokenForm),
    db: Session = Depends(get_db),
):
    """
    OAuth2 Token Endpoint
    - Supports Password Grant (username/password)
    - Supports Authorization Code Grant with PKCE (Alexa/public client)
    - Supports Device Code Grant
    - Supports Refresh Token Grant
    """
    gt = token_form.grant_type
    if gt == "password":
        return _handle_password_grant(token_form, db)
    elif gt == "authorization_code":
        return _handle_auth_code_grant(request, token_form, db)
    elif gt == "urn:ietf:params:oauth:grant-type:device_code":
        return _handle_device_code_grant(token_form, db)
    elif gt == "refresh_token":
        return _handle_refresh_token_grant(token_form, db)
    else:
        raise HTTPException(status_code=400, detail="unsupported_grant_type")

@router.post("/devicecode", response_model=DeviceCodeResponse)
async def authorize_device(
        request: Request,
        device_form: OAuth2DeviceCodeForm = Depends(OAuth2DeviceCodeForm),
        db: Session = Depends(get_db),
) -> DeviceCodeResponse:
    device_code = secrets.token_urlsafe(32)
    user_code = secrets.token_urlsafe(8)
    verification_uri = str(settings.OAUTH_DEVICE_VERIFICATION_URI)
    verification_uri_complete = f"{settings.OAUTH_DEVICE_VERIFICATION_URI}?user_code={user_code}"

    # Save device credential in DB (replaces in-memory DEVICE_CODES)
    cred = DeviceCredential(
        client_id=device_form.client_id,
        scope=device_form.scope or "",
        device_code=device_code,
        user_code=user_code,
        expires_at=int(time.time()) + 1800,
        interval=5,
        status="pending",
    )
    db.add(cred)
    db.commit()

    return DeviceCodeResponse(
        device_code=device_code,
        user_code=user_code,
        verification_uri=verification_uri,
        verification_uri_complete=verification_uri_complete,
        expires_in=1800,
        interval=5,
        message="Please visit the verification URI to authorize the device",
    )


@router.post("/auth")
async def authorize(
    request: Request,
    form: OAuthAuthorizeForm = Depends(OAuthAuthorizeForm),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Support both form-encoded and query parameters (fallback)
    response_type = form.response_type or request.query_params.get("response_type")
    client_id = form.client_id or request.query_params.get("client_id")
    redirect_uri = form.redirect_uri or request.query_params.get("redirect_uri")
    state = form.state or request.query_params.get("state", "")
    scope = form.scope or request.query_params.get("scope", "")
    code_challenge = form.code_challenge or request.query_params.get("code_challenge")
    code_challenge_method = form.code_challenge_method or request.query_params.get("code_challenge_method", "S256")
    client_secret = form.client_secret or request.query_params.get("client_secret")

    if response_type != "code":
        raise HTTPException(status_code=400, detail="unsupported_response_type")
    if not code_challenge:
        raise HTTPException(status_code=400, detail="Missing code_challenge (PKCE required)")

    _validate_redirect_uri(redirect_uri)
    _validate_client(client_id, client_secret)

    code = secrets.token_urlsafe(32)
    # Persist authorization code in DB
    ac = OAuth2AuthorizationCode(
        code=code,
        client_id=client_id,
        redirect_uri=redirect_uri,
        response_type="code",
        scope=scope or "",
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method or "S256",
        user_id=current_user.id,
    )
    db.add(ac)
    db.commit()

    return RedirectResponse(url=f"{redirect_uri}?code={code}&state={state}", status_code=302)


@router.post("/auth-json", response_model=AuthJsonResponse)
async def authorizeJson(
    request: Request,
    form: OAuthAuthorizeForm = Depends(OAuthAuthorizeForm),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> AuthJsonResponse:
    # Support both form-encoded and query parameters (fallback)
    response_type = form.response_type or request.query_params.get("response_type")
    client_id = form.client_id or request.query_params.get("client_id")
    redirect_uri = form.redirect_uri or request.query_params.get("redirect_uri")
    state = form.state or request.query_params.get("state", "")
    scope = form.scope or request.query_params.get("scope", "")
    code_challenge = form.code_challenge or request.query_params.get("code_challenge")
    code_challenge_method = form.code_challenge_method or request.query_params.get("code_challenge_method", "S256")
    client_secret = form.client_secret or request.query_params.get("client_secret")

    if response_type != "code":
        raise HTTPException(status_code=400, detail="unsupported_response_type")
    if not code_challenge:
        raise HTTPException(status_code=400, detail="Missing code_challenge (PKCE required)")

    _validate_redirect_uri(redirect_uri)
    _validate_client(client_id, client_secret)

    code = secrets.token_urlsafe(32)
    ac = OAuth2AuthorizationCode(
        code=code,
        client_id=client_id,
        redirect_uri=redirect_uri,
        response_type="code",
        scope=scope or "",
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method or "S256",
        user_id=current_user.id,
    )
    db.add(ac)
    db.commit()

    return AuthJsonResponse(redirect_to=f"{redirect_uri}?code={code}&state={state}")


@router.post("/device/verify", response_model=DeviceVerificationResponse)
async def verify_device_code(
    request: Request,
    form: DeviceVerifyForm = Depends(DeviceVerifyForm),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceVerificationResponse:
    """
    Verify a device by entering the `user_code` on the verification page.
    Uses application/x-www-form-urlencoded form data.
    """
    user_code = (form.user_code or "").strip() if form.user_code else ""
    if not user_code:
        # Fallback: try to read from query for convenience
        user_code = (request.query_params.get("user_code") or "").strip()
    if not user_code:
        raise HTTPException(status_code=400, detail="invalid_request")

    # Find device credential by user_code in DB
    cred = db.exec(select(DeviceCredential).where(DeviceCredential.user_code == user_code)).first()
    if not cred:
        raise HTTPException(status_code=400, detail="bad_verification_code")

    # Expired?
    if cred.expires_at and cred.expires_at <= int(time.time()):
        cred.status = "expired"
        db.add(cred)
        db.commit()
        raise HTTPException(status_code=400, detail="expired_token")

    # If already denied
    if cred.status == "denied":
        raise HTTPException(status_code=400, detail="authorization_declined")

    # Only allow when pending
    if cred.status not in {"pending", "authorized"}:
        raise HTTPException(status_code=400, detail="invalid_request")

    if not cred.client_id:
        raise HTTPException(status_code=400, detail="invalid_request")

    if form.approve is False:
        cred.status = "denied"
        db.add(cred)
        db.commit()
        return {"status": "denied"}

    # Attach user and mark authorized
    cred.status = "authorized"
    cred.user_id = current_user.id
    db.add(cred)
    db.commit()

    # Create a linked Device in DB for traceability
    #Check if device already exists
    dev = db.exec(select(Device).where(Device.device_id == cred.client_id)).first()
    if dev:
        if dev.owner_id != current_user.id:
            raise HTTPException(status_code=400, detail="invalid_grant")
        return DeviceVerificationResponse(
            status="authorized",
            device_id=dev.id,
            device=DeviceInfo(id=dev.id, name=dev.name, type=dev.type),
            client_id=cred.client_id,
            scope=cred.scope or "",
        )

    dev = Device(
        name=form.name or "Linked Device",
        type="",
        status=DeviceStatus.ONLINE,
        is_active=True,
        owner_id=current_user.id,
        device_id=cred.client_id,
    )
    db.add(dev)
    db.commit()
    db.refresh(dev)

    return DeviceVerificationResponse(
        status="authorized",
        device_id=dev.id,
        device=DeviceInfo(id=dev.id, name=dev.name, type=dev.type),
        client_id=cred.client_id,
        scope=cred.scope or "",
    )
