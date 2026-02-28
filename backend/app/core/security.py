from typing import Annotated

import jwt
import requests
from fastapi import Depends, HTTPException, status
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

def get_jwks_client():
    global _jwks_client
    if _jwks_client is None:
        jwks_url = settings.OIDC_JWKS_URL
        if not jwks_url:
            # Try OIDC discovery
            try:
                discovery_url = settings.OIDC_ISSUER.rstrip("/") + "/.well-known/openid-configuration"
                response = requests.get(discovery_url, timeout=5)
                response.raise_for_status()
                jwks_url = response.json()["jwks_uri"]
            except Exception:
                # Fallback for Zitadel/generic
                jwks_url = settings.OIDC_ISSUER.rstrip("/") + "/oauth/v2/keys"
        
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


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Session = Depends(get_db)
) -> User:
    try:
        data = validate_oidc_token(token)

        sub = data.get("sub")
        if not sub:
            raise ValueError("Missing sub claim")

        # Find user by oidc_sub
        user = session.exec(select(User).where(User.oidc_sub == sub)).first()
        
        if not user:
            # Create user on the fly if not exists
            user = User(
                email=data.get("email"),
                username=data.get("preferred_username") or data.get("email"),
                is_active=True,
                is_superuser=False,
                oidc_sub=sub
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        return user
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