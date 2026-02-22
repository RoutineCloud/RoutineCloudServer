from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.security import get_current_active_superuser
from app.db.session import get_db
from app.models.oauth2 import OAuth2Client
from app.schemas.oauth2 import OAuth2ClientRead, OAuth2ClientUpdate

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_active_superuser)],
    responses={404: {"description": "Not found"}},
)

@router.get("/oauth/clients", response_model=List[OAuth2ClientRead], operation_id="admin_list_oauth_clients")
async def list_oauth_clients(
    *,
    session: Session = Depends(get_db)
):
    """
    List all OAuth2 clients.
    """
    clients = session.exec(select(OAuth2Client)).all()
    return clients

@router.get("/oauth/clients/{client_id}", response_model=OAuth2ClientRead, operation_id="admin_get_oauth_client")
async def get_oauth_client(
    *,
    session: Session = Depends(get_db),
    client_id: int
):
    """
    Get a specific OAuth2 client by ID.
    """
    client = session.get(OAuth2Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="OAuth2 client not found")
    return client

@router.put("/oauth/clients/{client_id}", response_model=OAuth2ClientRead, operation_id="admin_update_oauth_client")
async def update_oauth_client(
    *,
    session: Session = Depends(get_db),
    client_id: int,
    client_in: OAuth2ClientUpdate
):
    """
    Update an OAuth2 client.
    """
    db_obj = session.get(OAuth2Client, client_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="OAuth2 client not found")
    
    update_data = client_in.model_dump(exclude_unset=True)
    
    if "client_metadata" in update_data:
        db_obj.set_client_metadata(update_data.pop("client_metadata"))
    
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj

@router.delete("/oauth/clients/{client_id}", operation_id="admin_delete_oauth_client")
async def delete_oauth_client(
    *,
    session: Session = Depends(get_db),
    client_id: int
):
    """
    Delete an OAuth2 client.
    """
    client = session.get(OAuth2Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="OAuth2 client not found")
    
    session.delete(client)
    session.commit()
    return {"message": "OAuth2 client deleted successfully"}
