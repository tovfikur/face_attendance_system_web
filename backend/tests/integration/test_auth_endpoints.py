"""Integration tests for authentication API endpoints."""

import json
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import Role, User


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db_session():
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as session:
        # Create test roles
        admin_role = Role(
            id="ROLE-ADMIN",
            name="Admin",
            permissions=json.dumps(["*"]),
            description="Full system access",
        )
        operator_role = Role(
            id="ROLE-OPERATOR",
            name="Operator",
            permissions=json.dumps(["cameras:read", "attendance:read"]),
            description="Operator access",
        )

        session.add(admin_role)
        session.add(operator_role)

        # Create test users
        admin_user = User(
            id=str(uuid4()),
            email="admin@example.com",
            name="Admin User",
            hashed_password=hash_password("admin123"),
            role_id="ROLE-ADMIN",
            status="active",
        )

        operator_user = User(
            id=str(uuid4()),
            email="operator@example.com",
            name="Operator User",
            hashed_password=hash_password("operator123"),
            role_id="ROLE-OPERATOR",
            status="active",
        )

        session.add(admin_user)
        session.add(operator_user)
        await session.commit()

        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def client(test_db_session):
    """Create a test client with test database."""
    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()


class TestAuthLogin:
    """Tests for login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success_with_admin(self, client):
        """Test successful admin login."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin@example.com", "password": "admin123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "accessToken" in data["data"]
        assert "refreshToken" in data["data"]
        assert "user" in data["data"]
        assert data["data"]["user"]["email"] == "admin@example.com"
        assert data["data"]["user"]["roleId"] == "ROLE-ADMIN"

    @pytest.mark.asyncio
    async def test_login_success_with_operator(self, client):
        """Test successful operator login."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "operator@example.com", "password": "operator123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "accessToken" in data["data"]
        assert "refreshToken" in data["data"]
        assert data["data"]["user"]["roleId"] == "ROLE-OPERATOR"

    @pytest.mark.asyncio
    async def test_login_with_invalid_email(self, client):
        """Test login with non-existent email."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent@example.com", "password": "password123"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.asyncio
    async def test_login_with_incorrect_password(self, client):
        """Test login with incorrect password."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_login_with_empty_username(self, client):
        """Test login with empty username."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "", "password": "admin123"},
        )

        # Should be either 400 or 422 for validation error
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_login_with_empty_password(self, client):
        """Test login with empty password."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin@example.com", "password": ""},
        )

        # Should be either 400 or 422 for validation error
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_login_with_missing_fields(self, client):
        """Test login with missing required fields."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin@example.com"},  # Missing password
        )

        assert response.status_code == 422


class TestAuthRefresh:
    """Tests for token refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client):
        """Test successful token refresh."""
        # First, login to get a refresh token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin@example.com", "password": "admin123"},
        )

        refresh_token = login_response.json()["data"]["refreshToken"]

        # Now refresh the token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refreshToken": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "accessToken" in data["data"]
        assert "refreshToken" in data["data"]

    @pytest.mark.asyncio
    async def test_refresh_token_with_invalid_token(self, client):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refreshToken": "invalid.token.here"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_refresh_token_with_empty_token(self, client):
        """Test refresh with empty token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refreshToken": ""},
        )

        # Should fail with invalid token
        assert response.status_code in [400, 401, 422]


class TestAuthLogout:
    """Tests for logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(self, client):
        """Test successful logout."""
        # First, login to get a refresh token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin@example.com", "password": "admin123"},
        )

        refresh_token = login_response.json()["data"]["refreshToken"]

        # Now logout
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refreshToken": refresh_token},
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_logout_with_invalid_token(self, client):
        """Test logout with invalid token."""
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refreshToken": "invalid.token.here"},
        )

        # Should succeed silently or fail gracefully
        assert response.status_code in [200, 204, 401]


class TestAuthMe:
    """Tests for get current user endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, client):
        """Test getting current user with valid token."""
        # First, login to get a token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin@example.com", "password": "admin123"},
        )

        access_token = login_response.json()["data"]["accessToken"]

        # Get current user
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "admin@example.com"
        assert data["data"]["roleId"] == "ROLE-ADMIN"

    @pytest.mark.asyncio
    async def test_get_current_user_without_token(self, client):
        """Test getting current user without token."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_with_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_with_malformed_header(self, client):
        """Test with malformed authorization header."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "InvalidFormat token"},
        )

        assert response.status_code == 401


class TestAuthPassword:
    """Tests for password change endpoint."""

    @pytest.mark.asyncio
    async def test_change_password_success(self, client):
        """Test successful password change."""
        # First, login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin@example.com", "password": "admin123"},
        )

        access_token = login_response.json()["data"]["accessToken"]

        # Change password
        response = await client.patch(
            "/api/v1/auth/password",
            json={
                "currentPassword": "admin123",
                "newPassword": "newpassword123",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_change_password_with_wrong_current_password(self, client):
        """Test password change with incorrect current password."""
        # First, login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin@example.com", "password": "admin123"},
        )

        access_token = login_response.json()["data"]["accessToken"]

        # Try to change password with wrong current password
        response = await client.patch(
            "/api/v1/auth/password",
            json={
                "currentPassword": "wrongpassword",
                "newPassword": "newpassword123",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_change_password_without_token(self, client):
        """Test password change without authentication."""
        response = await client.patch(
            "/api/v1/auth/password",
            json={
                "currentPassword": "admin123",
                "newPassword": "newpassword123",
            },
        )

        assert response.status_code == 401


class TestRolesEndpoint:
    """Tests for roles endpoint."""

    @pytest.mark.asyncio
    async def test_get_roles_success(self, client):
        """Test getting roles list."""
        # First, login to get a token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin@example.com", "password": "admin123"},
        )

        access_token = login_response.json()["data"]["accessToken"]

        # Get roles
        response = await client.get(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 2  # At least admin and operator roles

    @pytest.mark.asyncio
    async def test_get_roles_without_token(self, client):
        """Test getting roles without authentication."""
        response = await client.get("/api/v1/roles")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_roles_contains_admin_role(self, client):
        """Test that roles list contains admin role."""
        # First, login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin@example.com", "password": "admin123"},
        )

        access_token = login_response.json()["data"]["accessToken"]

        # Get roles
        response = await client.get(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        data = response.json()
        roles = data["data"]
        admin_role = next((r for r in roles if r["id"] == "ROLE-ADMIN"), None)

        assert admin_role is not None
        assert admin_role["name"] == "Admin"
        assert "*" in admin_role["permissions"]
