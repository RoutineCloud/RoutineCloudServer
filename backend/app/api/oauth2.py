from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request, Response, HTTPException, status

from app.core.oauth2 import authorization
from app.core.security import OAuth2TokenForm, OAuth2DeviceCodeForm, DeviceVerifyForm, get_current_user
from app.db.session import get_db
from app.models.device import Device, DeviceStatus
from app.models.oauth2 import OAuth2DeviceCodes
from app.models.user import User
from app.schemas.security import TokenResponse, DeviceCodeResponse, DeviceVerificationResponse, DeviceInfo

router = APIRouter(
    prefix="/api/oauth",
    tags=["oauth2"],
    responses={404: {"description": "Not found"}},
)

@router.post('/token', response_model=TokenResponse)
async def token(
        request: Request,
        response: Response,
        token_form: OAuth2TokenForm = Depends(OAuth2TokenForm)
        ):
    request.state.oauth2_form = token_form

    status, body, headers = authorization.create_token_response(request=request)
    response.headers.update(dict(headers))
    response.status_code = status
    return TokenResponse(**body)


@router.post('/device_authorization', response_model=DeviceCodeResponse)
async def device_authorization(
        request: Request,
        response: Response,
        form: OAuth2DeviceCodeForm = Depends(OAuth2DeviceCodeForm)
):
    request.state.oauth2_form = form
    status_code, body, headers = authorization.create_endpoint_response('device_authorization', request=request)
    response.headers.update(dict(headers))
    response.status_code = status_code
    body["message"] = "Please visit the verification page and enter the code:"
    return DeviceCodeResponse(**body)


@router.post('/device/verify', response_model=DeviceVerificationResponse)
async def device_verify(
        form: DeviceVerifyForm = Depends(DeviceVerifyForm),
        current_user: User = Depends(get_current_user),
):
    if not form.user_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_code is required")

    session = next(get_db())
    cred = session.query(OAuth2DeviceCodes).filter_by(user_code=form.user_code).first()
    if not cred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invalid_user_code")

    if cred.is_expired():
        session.delete(cred)
        session.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="code_expired")

    # attach decision to this credential
    cred.user_id = current_user.id
    cred.status = 'granted' if form.approve else 'denied'
    session.add(cred)
    session.commit()
    if not form.approve:
        return DeviceVerificationResponse(status='denied', client_id=cred.client_id, scope=cred.scope)

    # If a device_uuid was provided at device_authorization, clean up older entries
    # with the same uuid that also belong to the current user. This prevents having
    # multiple active device_code records for the same physical device per user.
    if getattr(cred, 'device_uuid', None):
        # Also, if a Device with same uuid exists for current user, delete it to avoid duplicates
        try:
            existing_devices = (
                session.query(Device)
                .filter(Device.device_id == cred.device_uuid, Device.owner_id == current_user.id)
                .all()
            )
            for d in existing_devices:
                session.delete(d)
            session.commit()
        except Exception:
            session.rollback()

    # Create a linked Device in DB for traceability
    dev = Device(
        name=form.name or "Linked Device",
        type="",
        status=DeviceStatus.ONLINE,
        is_active=True,
        owner_id=current_user.id,
        device_id=cred.device_uuid or "",
    )
    session.add(dev)
    session.commit()
    session.refresh(dev)

    return DeviceVerificationResponse(
        status='authorized',
        device_id=dev.id,
        device=DeviceInfo(id=dev.id, name=dev.name, type=dev.type, uuid=dev.device_id or ""),
        client_id=cred.client_id,
        scope=cred.scope,
    )
