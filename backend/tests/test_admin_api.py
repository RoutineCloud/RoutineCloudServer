from fastapi.testclient import TestClient

def test_admin_list_oauth_clients_superuser(client: TestClient, superuser_token: str):
    response = client.get(
        "/api/admin/oauth/clients",
        headers={"Authorization": f"Bearer {superuser_token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_admin_list_oauth_clients_normal_user(client: TestClient, normal_user_token: str):
    response = client.get(
        "/api/admin/oauth/clients",
        headers={"Authorization": f"Bearer {normal_user_token}"},
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "The user doesn't have enough privileges"}

def test_admin_list_oauth_clients_unauthenticated(client: TestClient):
    response = client.get("/api/admin/oauth/clients")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

def test_admin_get_oauth_client_superuser_not_found(client: TestClient, superuser_token: str):
    response = client.get(
        "/api/admin/oauth/clients/999",
        headers={"Authorization": f"Bearer {superuser_token}"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "OAuth2 client not found"}

def test_admin_list_oauth_clients_content(client: TestClient, superuser_token: str, session):
    from app.models.oauth2 import OAuth2Client
    
    test_client = OAuth2Client(client_id="test-id", client_secret="test-secret")
    test_client.set_client_metadata({"client_name": "Test Client"})
    session.add(test_client)
    session.commit()
    
    response = client.get(
        "/api/admin/oauth/clients",
        headers={"Authorization": f"Bearer {superuser_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(c["client_id"] == "test-id" for c in data)

def test_admin_delete_oauth_client_superuser(client: TestClient, superuser_token: str, session):
    from app.models.oauth2 import OAuth2Client
    
    test_client = OAuth2Client(client_id="delete-me", client_secret="secret")
    session.add(test_client)
    session.commit()
    session.refresh(test_client)
    client_id = test_client.id
    
    response = client.delete(
        f"/api/admin/oauth/clients/{client_id}",
        headers={"Authorization": f"Bearer {superuser_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "OAuth2 client deleted successfully"}
    
    # Verify it's gone
    assert session.get(OAuth2Client, client_id) is None

def test_admin_delete_oauth_client_normal_user(client: TestClient, normal_user_token: str, session):
    from app.models.oauth2 import OAuth2Client
    
    test_client = OAuth2Client(client_id="dont-delete-me", client_secret="secret")
    session.add(test_client)
    session.commit()
    session.refresh(test_client)
    client_id = test_client.id
    
    response = client.delete(
        f"/api/admin/oauth/clients/{client_id}",
        headers={"Authorization": f"Bearer {normal_user_token}"},
    )
    assert response.status_code == 403
    
    # Verify it's still there
    assert session.get(OAuth2Client, client_id) is not None
