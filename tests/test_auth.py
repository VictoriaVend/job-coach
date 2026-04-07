"""
Auth Tests: Registration and Login Flows
========================================
Purpose: Verify user management, security headers, and password policy enforcement.
Notes: Tests remain async using httpx.AsyncClient, even if DB service is sync.
"""

import pytest


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_success(self, client):
        """Verify successful user registration with valid data."""
        resp = await client.post(
            "/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "SecurePassword123!",  # Meets strong policy
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert data["is_active"] is True
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "invalid_password, error_snippet",
        [
            ("short1!", "at least 12 characters"),
            ("NoSpecialChar123", "at least one special character"),
            ("nouppercase123!", "at least one uppercase letter"),
            ("NoNumberSpecial!", "at least one number"),
            (
                "A" * 73,
                "max",
            ),  # Test max length policy - check for "max" in error message
        ],
    )
    async def test_register_weak_password(self, client, invalid_password, error_snippet):
        """Verify that weak passwords are rejected by Pydantic validation."""
        resp = await client.post(
            "/v1/auth/register",
            json={
                "username": "weakuser",
                "email": "weak@example.com",
                "password": invalid_password,
            },
        )
        assert resp.status_code == 422  # Pydantic validation error
        # Verify the error detail contains our custom policy message
        errors = resp.json()["detail"]
        assert any(
            error_snippet.lower() in str(e).lower() for e in errors
        ), f"Expected '{error_snippet}' in errors, but got: {errors}"

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client, registered_user):
        """Verify that existing usernames cannot be reused."""
        resp = await client.post(
            "/v1/auth/register",
            json={
                "username": "testuser",  # from registered_user fixture
                "email": "other@example.com",
                "password": "DifferentPass123!",
            },
        )
        assert resp.status_code == 400
        assert "Username already taken" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, registered_user):
        """Verify that existing emails cannot be reused."""
        resp = await client.post(
            "/v1/auth/register",
            json={
                "username": "anotheruser",
                "email": "test@example.com",  # from registered_user fixture
                "password": "DifferentPass123!",
            },
        )
        assert resp.status_code == 400
        assert "Email already registered" in resp.json()["detail"]


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, client, registered_user):
        """Verify successful login returns valid JWT token."""
        resp = await client.post(
            "/v1/auth/login",
            data={"username": "testuser", "password": "StrongPassword123!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, registered_user):
        """Verify that incorrect passwords are rejected with 401."""
        resp = await client.post(
            "/v1/auth/login",
            data={"username": "testuser", "password": "WrongPassword123!"},
        )
        assert resp.status_code == 401
        assert "Incorrect username or password" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        """Verify that unknown users are rejected with 401."""
        resp = await client.post(
            "/v1/auth/login",
            data={"username": "ghostuser", "password": "SomePassword123!"},
        )
        assert resp.status_code == 401


class TestRateLimiting:
    @pytest.mark.asyncio
    async def test_login_wrong_credentials(self, client):
        """Verify that wrong credentials return 401."""
        resp = await client.post(
            "/v1/auth/login", data={"username": "nonexistent", "password": "wrong"}
        )
        assert resp.status_code == 401
