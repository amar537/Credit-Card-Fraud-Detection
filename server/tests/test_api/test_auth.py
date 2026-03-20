import pytest


def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/api/v1/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "NewPassword123!",
            "full_name": "New User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"


def test_register_duplicate_email(client):
    """Test registration with duplicate email."""
    # First registration
    client.post(
        "/api/v1/register",
        json={
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "Password123!",
        }
    )
    
    # Try to register again with same email
    response = client.post(
        "/api/v1/register",
        json={
            "email": "duplicate@example.com",
            "username": "user2",
            "password": "Password123!",
        }
    )
    assert response.status_code == 400 or response.status_code == 409


def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post(
        "/api/v1/login",
        json={"email": "test@example.com", "password": "TestPassword123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["email"] == "test@example.com"


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post(
        "/api/v1/login",
        json={"email": "nonexistent@example.com", "password": "WrongPassword123!"}
    )
    assert response.status_code == 401 or response.status_code == 404


def test_get_current_user(client, auth_headers):
    """Test getting current user info."""
    response = client.get("/api/v1/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "username" in data


def test_get_current_user_unauthorized(client):
    """Test getting current user without authentication."""
    response = client.get("/api/v1/me")
    assert response.status_code == 401


def test_refresh_token(client, test_user):
    """Test token refresh."""
    # First login
    login_response = client.post(
        "/api/v1/login",
        json={"email": "test@example.com", "password": "TestPassword123!"}
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # Refresh token
    response = client.post(
        "/api/v1/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_refresh_token_invalid(client):
    """Test refresh with invalid token."""
    response = client.post(
        "/api/v1/refresh",
        json={"refresh_token": "invalid_token"}
    )
    assert response.status_code == 401


def test_logout(client, auth_headers):
    """Test logout."""
    response = client.post("/api/v1/logout", headers=auth_headers)
    assert response.status_code == 200
    assert "message" in response.json()


def test_update_profile(client, auth_headers):
    """Test updating user profile."""
    response = client.put(
        "/api/v1/me",
        headers=auth_headers,
        json={"full_name": "Updated Name", "username": "updateduser"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["username"] == "updateduser"


def test_change_password(client, auth_headers, test_user):
    """Test changing password."""
    response = client.post(
        "/api/v1/change-password",
        headers=auth_headers,
        json={
            "current_password": "TestPassword123!",
            "new_password": "NewPassword123!"
        }
    )
    assert response.status_code == 200
    assert "message" in response.json()
    
    # Verify old password no longer works
    login_response = client.post(
        "/api/v1/login",
        json={"email": "test@example.com", "password": "TestPassword123!"}
    )
    assert login_response.status_code != 200
    
    # Verify new password works
    login_response = client.post(
        "/api/v1/login",
        json={"email": "test@example.com", "password": "NewPassword123!"}
    )
    assert login_response.status_code == 200

