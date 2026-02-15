from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.device import Device
from app.models.user import User
from app.schemas.device import DeviceRead

# Create router
router = APIRouter(
    prefix="/api/devices",
    tags=["devices"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[DeviceRead], operation_id="devices_list")
async def list_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all devices that belong to the authenticated user."""
    devices = db.exec(select(Device).where(Device.owner_id == current_user.id)).all()
    return devices


@router.get("/{device_id}", response_model=DeviceRead, operation_id="devices_get")
async def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a single device by ID if it belongs to the authenticated user."""
    dev: Optional[Device] = db.exec(
        select(Device).where(Device.id == device_id, Device.owner_id == current_user.id)
    ).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found")
    return dev
