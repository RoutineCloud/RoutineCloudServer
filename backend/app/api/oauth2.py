from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from app.core.config import settings
from app.core.oauth2 import authorization
from app.core.security import OAuth2TokenForm, OAuth2DeviceCodeForm, DeviceVerifyForm, OAuthAuthorizeForm, \
    get_session_user
from app.db.session import get_db
from app.models.device import Device, DeviceStatus
from app.models.oauth2 import OAuth2DeviceCodes, OAuthConsent, OAuth2Client
from app.models.user import User
from app.schemas.oauth2 import OAuth2ConsentInfo, OAuth2ScopeInfo
from app.schemas.security import TokenResponse, DeviceCodeResponse, DeviceVerificationResponse, DeviceInfo, \
    AuthJsonResponse

router = APIRouter(
    prefix="/api/oauth",
    tags=["oauth2"],
    responses={404: {"description": "Not found"}},
)

SCOPE_MAPPING = {
    "routinecloud": {
        "name": "Access Routine Cloud",
        "description": "Full access to your Routine Cloud account, including routines and devices."
    }
}


@router.post('/token', response_model=TokenResponse, operation_id="oauth_token")
async def token(
        request: Request,
        response: Response,
        db: Session = Depends(get_db),
        token_form: OAuth2TokenForm = Depends(OAuth2TokenForm)
        ):
    request.state.db = db
    request.state.oauth2_form = token_form

    status, body, headers = authorization.create_token_response(request=request)
    response.headers.update(dict(headers))
    response.status_code = status
    
    return TokenResponse(**body)


@router.get('/authorize', operation_id="oauth_authorize")
async def authorize(
        request: Request,
        response: Response,
        db: Session = Depends(get_db),
        form: OAuthAuthorizeForm = Depends(OAuthAuthorizeForm),
        current_user: Optional[User] = Depends(get_session_user),

):
    request.state.db = db
    request.state.oauth2_form = form

    # 1. Check login status
    if not current_user:
        # Redirect to frontend login page
        # We pass the full original URL so the frontend can redirect back here
        return_url = str(request.url)
        # URL encode the return_url for safety
        login_url = f"{settings.FRONTEND_URL}{settings.LOGIN_PATH}?redirect={quote(return_url)}"
        return RedirectResponse(url=login_url)

    # 2. Check if user has already allowed this client and scope
    consent = db.query(OAuthConsent).filter_by(
        user_id=current_user.id,
        client_id=form.client_id
    ).first()

    # If no existing consent or it's revoked, we definitely need consent page
    if not consent or (consent.revoked_at is not None):
        # Redirect to frontend consent page
        # We pass all the OAuth parameters
        consent_url = f"{settings.FRONTEND_URL}{settings.AUTHORIZE_PATH}?{request.query_params}"
        return RedirectResponse(url=consent_url)

    # 3. If logged in and already consented, we can issue the code immediately
    # We pass the logged-in user to Authlib as the 'grant_user'
    status, body, headers = authorization.create_authorization_response(
        request=request, grant_user=current_user
    )
    if status == 302:
        response.headers.update(dict(headers))
        response.status_code = status
        return response
    
    # Fallback (should not happen if parameters are valid)
    return RedirectResponse(url=f"{settings.FRONTEND_URL}{settings.AUTHORIZE_PATH}?{request.query_params}")


@router.get('/consent', response_model=OAuth2ConsentInfo, operation_id="oauth_get_consent_info")
async def get_consent_info(
        request: Request,
        db: Session = Depends(get_db),
        form: OAuthAuthorizeForm = Depends(OAuthAuthorizeForm),
        current_user: User = Depends(get_session_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not logged in")

    client: OAuth2Client = db.query(OAuth2Client).filter_by(client_id=form.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    requested_scopes = form.scope.split()
    scopes_info = []
    for s in requested_scopes:
        if s in SCOPE_MAPPING:
            scopes_info.append(OAuth2ScopeInfo(
                id=s,
                name=SCOPE_MAPPING[s]["name"],
                description=SCOPE_MAPPING[s]["description"]
            ))
        else:
            # Fallback for unknown scopes
            scopes_info.append(OAuth2ScopeInfo(
                id=s,
                name=s,
                description=f"Permission to access {s}"
            ))

    return OAuth2ConsentInfo(
        client_name=client.client_name,
        scopes=scopes_info
    )


@router.post('/consent', response_model=AuthJsonResponse, operation_id="oauth_consent")
async def oauth_consent(
        request: Request,
        db: Session = Depends(get_db),
        form: OAuthAuthorizeForm = Depends(OAuthAuthorizeForm),
        current_user: User = Depends(get_session_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not logged in")
    request.state.db = db
    request.state.oauth2_form = form

    # 1. Save or update consent
    existing_consent = db.query(OAuthConsent).filter_by(
        user_id=current_user.id,
        client_id=form.client_id
    ).first()

    if existing_consent:
        existing_consent.scopes = form.scope
        existing_consent.revoked_at = None
        db.add(existing_consent)
    else:
        new_consent = OAuthConsent(
            user_id=current_user.id,
            client_id=form.client_id,
            scopes=form.scope
        )
        db.add(new_consent)

    db.commit()

    # 2. Redirect back to the authorize endpoint to complete the authorization flow
    # This keeps the final authorization logic centralized in the authorize endpoint.
    # We use url_for to get the absolute URL to the authorize endpoint.
    authorize_url = str(request.url_for("authorize"))
    if request.query_params:
        authorize_url += f"?{request.query_params}"
    return AuthJsonResponse(redirect_to=authorize_url)


@router.post('/device_authorization', response_model=DeviceCodeResponse, operation_id="oauth_device_authorization")
async def device_authorization(
        request: Request,
        response: Response,
        db: Session = Depends(get_db),
        form: OAuth2DeviceCodeForm = Depends(OAuth2DeviceCodeForm)
):
    request.state.db = db
    request.state.oauth2_form = form
    status_code, body, headers = authorization.create_endpoint_response('device_authorization', request=request)
    response.headers.update(dict(headers))
    response.status_code = status_code
    body["message"] = "Please visit the verification page and enter the code:"
    return DeviceCodeResponse(**body)


@router.post('/device/verify', response_model=DeviceVerificationResponse, operation_id="oauth_device_verify")
async def device_verify(
        db: Session = Depends(get_db),
        form: DeviceVerifyForm = Depends(DeviceVerifyForm),
        current_user: User = Depends(get_session_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not logged in")
    if not form.user_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_code is required")

    cred = db.query(OAuth2DeviceCodes).filter_by(user_code=form.user_code).first()
    if not cred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invalid_user_code")

    if cred.is_expired():
        db.delete(cred)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="code_expired")

    # attach decision to this credential
    cred.user_id = current_user.id
    cred.status = 'granted' if form.approve else 'denied'
    db.add(cred)
    db.commit()
    if not form.approve:
        return DeviceVerificationResponse(status='denied', client_id=cred.client_id, scope=cred.scope)

    # If a device_uuid was provided at device_authorization, clean up older entries
    # with the same uuid that also belong to the current user. This prevents having
    # multiple active device_code records for the same physical device per user.
    if getattr(cred, 'device_uuid', None):
        # Also, if a Device with same uuid exists for current user, delete it to avoid duplicates
        try:
            existing_devices = (
                db.query(Device)
                .filter(Device.device_id == cred.device_uuid, Device.owner_id == current_user.id)
                .all()
            )
            for d in existing_devices:
                db.delete(d)
            db.commit()
        except Exception:
            db.rollback()

    # Create a linked Device in DB for traceability
    dev = Device(
        name=form.name or "Linked Device",
        type="",
        status=DeviceStatus.ONLINE,
        is_active=True,
        owner_id=current_user.id,
        device_id=cred.device_uuid or "",
    )
    db.add(dev)
    db.commit()
    db.refresh(dev)

    return DeviceVerificationResponse(
        status='authorized',
        device_id=dev.id,
        device=DeviceInfo(id=dev.id, name=dev.name, type=dev.type, uuid=dev.device_id or ""),
        client_id=cred.client_id,
        scope=cred.scope,
    )
