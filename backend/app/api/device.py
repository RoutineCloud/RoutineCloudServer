from fastapi import APIRouter, status
from typing import List

from app.schemas.device import DeviceCreate, DeviceRead, DeviceUpdate, DeviceStatus

# Create router
router = APIRouter(
    prefix="/api/devices",
    tags=["devices"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[DeviceRead], operation_id="devices_list")
async def get_devices():
    """
    Get all devices for the current user
    """
    # This would fetch devices from the database in a real app
    return [
        {"id": 1, "name": "Living Room Light", "type": "light", "status": DeviceStatus.online, "is_active": True},
        {"id": 2, "name": "Kitchen Thermostat", "type": "thermostat", "status": DeviceStatus.online, "is_active": True},
        {"id": 3, "name": "Front Door Lock", "type": "lock", "status": DeviceStatus.offline, "is_active": True},
    ]


@router.get("/{device_id}", response_model=DeviceRead, operation_id="devices_get")
async def get_device(device_id: int):
    """
    Get a specific device by ID
    """
    # This would fetch the device from the database in a real app
    return {"id": device_id, "name": "Device Name", "type": "light", "status": DeviceStatus.online, "is_active": True}


@router.post("/", response_model=DeviceRead, status_code=status.HTTP_201_CREATED, operation_id="devices_create")
async def create_device(payload: DeviceCreate):
    """
    Create a new device
    """
    # In a real implementation, insert into DB and return created device
    return {"id": 4, "name": payload.name, "type": payload.type, "status": DeviceStatus.offline, "is_active": payload.is_active}


@router.put("/{device_id}", response_model=DeviceRead, operation_id="devices_update")
async def update_device(device_id: int, payload: DeviceUpdate):
    """
    Update a device
    """
    # In a real implementation, update DB and return updated device
    # For now, mock by echoing what would be updated
    base = {"id": device_id, "name": "Device Name", "type": "light", "status": DeviceStatus.online, "is_active": True}
    if payload.name is not None:
        base["name"] = payload.name
    if payload.type is not None:
        base["type"] = payload.type
    if payload.status is not None:
        base["status"] = payload.status
    if payload.is_active is not None:
        base["is_active"] = payload.is_active
    return base


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT, operation_id="devices_delete")
async def delete_device(device_id: int):
    """
    Delete a device
    """
    return None