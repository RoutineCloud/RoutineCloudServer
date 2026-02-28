from typing import Annotated, Optional

import jwt
import requests
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

# Use OAuth2PasswordBearer to allow testing via Swagger UI
# tokenUrl is not strictly necessary for OIDC flow, but good for UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWKS Client for validating tokens from OIDC provider
_jwks_client = None
_oidc_config = None

def get_oidc_config() -> dict:
    """Get OIDC configuration via discovery or fallback."""
    global _oidc_config
    if _oidc_config is None:
        try:
            discovery_url = settings.OIDC_ISSUER.rstrip("/") + "/.well-known/openid-configuration"
            response = requests.get(discovery_url, timeout=5)
            response.raise_for_status()
            _oidc_config = response.json()
        except Exception as e:
            print(f"OIDC discovery failed: {e}")
            # Minimal fallback for Zitadel or similar
            _oidc_config = {
                "jwks_uri": settings.OIDC_ISSUER.rstrip("/") + "/oauth/v2/keys",
                "userinfo_endpoint": settings.OIDC_ISSUER.rstrip("/") + "/oidc/v1/userinfo"
            }
    return _oidc_config

def get_jwks_client():
    global _jwks_client
    if _jwks_client is None:
        jwks_url = settings.OIDC_JWKS_URL
        if not jwks_url:
            jwks_url = get_oidc_config().get("jwks_uri")
        
        _jwks_client = jwt.PyJWKClient(jwks_url)
    return _jwks_client

def validate_oidc_token(token: str) -> dict:
    """Validate OIDC token and return decoded data."""
    jwks_client = get_jwks_client()
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
    except Exception as exc:
        print(f"Error fetching signing key: {exc}")
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    decode_params = {
        "jwt": token,
        "key": signing_key.key,
        "algorithms": ["RS256"],
        "issuer": settings.OIDC_ISSUER,
    }
    if settings.OIDC_CLIENT_ID:
        decode_params["audience"] = settings.OIDC_CLIENT_ID

    return jwt.decode(**decode_params)


def fetch_userinfo(token: str) -> dict:
    """Fetch userinfo from OIDC provider using access token."""
    endpoint = get_oidc_config().get("userinfo_endpoint")
    if not endpoint:
        raise ValueError("Userinfo endpoint not found in OIDC configuration")
    
    response = requests.get(
        endpoint,
        headers={"Authorization": f"Bearer {token}"},
        timeout=5
    )
    response.raise_for_status()
    return response.json()

def update_user_from_oidc_data(user: User, data: dict):
    """Update user model fields from OIDC data (either token or userinfo)."""
    if "email" in data:
        user.email = data["email"]
    
    # Try multiple keys for username
    username = data.get("preferred_username") or data.get("email") or data.get("name")
    if username:
        user.username = username

    # Check for Zitadel roles
    roles_claim = "urn:zitadel:iam:org:project:roles"
    roles = data.get(roles_claim)
    if roles:
        # Zitadel roles can be a dict or a list depending on configuration
        if isinstance(roles, dict):
            user.is_superuser = "admin" in roles
        elif isinstance(roles, list):
            user.is_superuser = "admin" in roles
    else:
        # If the claim is missing, we assume no roles (unless we want to preserve existing, 
        # but OIDC is the source of truth)
        user.is_superuser = False

def sync_user_with_oidc(session: Session, user: User, token: str) -> User:
    """Fetch userinfo and update user record."""
    try:
        user_info = fetch_userinfo(token)
        update_user_from_oidc_data(user, user_info)
        session.add(user)
        session.commit()
        session.refresh(user)
    except Exception as e:
        print(f"Failed to sync user with OIDC: {e}")
    return user

def get_or_create_user_from_oidc(session: Session, token: str, id_token: Optional[str] = None) -> User:
    """Validate OIDC token, find or create user and sync data."""
    # Use id_token for sub if available, otherwise fallback to access_token
    token_to_validate = id_token if id_token else token
    data = validate_oidc_token(token_to_validate)
    
    sub = data.get("sub")
    if not sub:
        raise ValueError("Missing sub claim in token")
    
    user = session.exec(select(User).where(User.oidc_sub == sub)).first()
    
    if not user:
        # Fetch detailed info from userinfo endpoint first
        try:
            user_info = fetch_userinfo(token)
            # Use userinfo data to supplement/override token data
            data.update(user_info)
        except Exception as e:
            print(f"Failed to fetch userinfo during user creation: {e}")

        # Create user on the fly if not exists
        user = User(
            oidc_sub=sub,
            is_active=True,
            is_superuser=False
        )
        update_user_from_oidc_data(user, data)
        session.add(user)
        session.commit()
        session.refresh(user)

    return user

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    id_token: Annotated[Optional[str], Header(alias="X-ID-Token")] = None,
    session: Session = Depends(get_db)
) -> User:
    try:
        return get_or_create_user_from_oidc(session, token, id_token=id_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_active_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user