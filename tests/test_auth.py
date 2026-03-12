"""Tests for auth endpoints: /auth/register, /auth/login."""


class TestRegister:
    def test_register_success(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "securepass",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert data["is_active"] is True
        assert "id" in data
        # Password must never be returned
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_username(self, client, registered_user):
        resp = client.post(
            "/auth/register",
            json={
                "username": "testuser",  # same as registered_user
                "email": "other@example.com",
                "password": "pass123",
            },
        )
        assert resp.status_code == 400
        assert "Username already taken" in resp.json()["detail"]

    def test_register_duplicate_email(self, client, registered_user):
        resp = client.post(
            "/auth/register",
            json={
                "username": "another",
                "email": "test@example.com",  # same as registered_user
                "password": "pass123",
            },
        )
        assert resp.status_code == 400
        assert "Email already registered" in resp.json()["detail"]

    def test_register_missing_fields(self, client):
        resp = client.post("/auth/register", json={"username": "x"})
        assert resp.status_code == 422  # validation error


class TestLogin:
    def test_login_success(self, client, registered_user):
        resp = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "strongpass123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, registered_user):
        resp = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "wrongpass"},
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post(
            "/auth/login",
            data={"username": "ghost", "password": "pass"},
        )
        assert resp.status_code == 401
