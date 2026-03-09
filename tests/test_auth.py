"""
Canal Educação v3.0 — Tests: Authentication & IAM
Integration tests for login, invite, confirm, RBAC.
"""


class TestBootstrap:

    def test_bootstrap_creates_admin(self, client):
        res = client.post("/api/v1/auth/bootstrap")
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "admin@canaleducacao.com"
        assert data["role"] == "admin"
        assert data["email_confirmed"] is True

    def test_bootstrap_fails_if_users_exist(self, client, admin_user):
        res = client.post("/api/v1/auth/bootstrap")
        assert res.status_code == 403


class TestLogin:

    def test_login_success(self, client, admin_user):
        res = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "admin123"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, admin_user):
        res = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "wrong"},
        )
        assert res.status_code == 401

    def test_login_nonexistent_user(self, client):
        res = client.post(
            "/api/v1/auth/login",
            data={"username": "nobody@test.com", "password": "test"},
        )
        assert res.status_code == 401

    def test_login_unconfirmed_user(self, client, db_session):
        from app.models.user import User
        from app.core.security import get_password_hash

        user = User(
            email="unconfirmed@test.com",
            full_name="Unconfirmed",
            role="assistente",
            hashed_password=get_password_hash("test123"),
            email_confirmed=False,
        )
        db_session.add(user)
        db_session.commit()

        res = client.post(
            "/api/v1/auth/login",
            data={"username": "unconfirmed@test.com", "password": "test123"},
        )
        assert res.status_code == 403
        assert "confirmado" in res.json()["detail"].lower()


class TestInvite:

    def test_admin_can_invite(self, client, admin_headers):
        res = client.post(
            "/api/v1/auth/invite",
            json={
                "email": "newuser@test.com",
                "full_name": "New User",
                "role": "assistente",
            },
            headers=admin_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "newuser@test.com"
        assert "invite_token" in data

    def test_assistant_cannot_invite(self, client, assistant_headers):
        res = client.post(
            "/api/v1/auth/invite",
            json={
                "email": "another@test.com",
                "full_name": "Another User",
                "role": "assistente",
            },
            headers=assistant_headers,
        )
        assert res.status_code == 403

    def test_duplicate_email_invite(self, client, admin_headers, assistant_user):
        res = client.post(
            "/api/v1/auth/invite",
            json={
                "email": "assistant@test.com",
                "full_name": "Duplicate",
                "role": "assistente",
            },
            headers=admin_headers,
        )
        assert res.status_code == 409


class TestConfirm:

    def test_confirm_account(self, client, admin_headers):
        # Create invite
        invite_res = client.post(
            "/api/v1/auth/invite",
            json={
                "email": "confirm@test.com",
                "full_name": "Confirm User",
                "role": "assistente",
            },
            headers=admin_headers,
        )
        token = invite_res.json()["invite_token"]

        # Confirm account
        res = client.post(
            "/api/v1/auth/confirm",
            json={"token": token, "password": "newpassword123"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["email_confirmed"] is True

        # Login with new password
        login_res = client.post(
            "/api/v1/auth/login",
            data={"username": "confirm@test.com", "password": "newpassword123"},
        )
        assert login_res.status_code == 200

    def test_confirm_invalid_token(self, client):
        res = client.post(
            "/api/v1/auth/confirm",
            json={"token": "invalid-token", "password": "password123"},
        )
        assert res.status_code == 404

    def test_confirm_short_password(self, client, admin_headers):
        invite_res = client.post(
            "/api/v1/auth/invite",
            json={
                "email": "shortpwd@test.com",
                "full_name": "Short Pwd",
                "role": "assistente",
            },
            headers=admin_headers,
        )
        token = invite_res.json()["invite_token"]

        res = client.post(
            "/api/v1/auth/confirm",
            json={"token": token, "password": "short"},
        )
        assert res.status_code == 422  # Pydantic validation


class TestMe:

    def test_get_me(self, client, admin_headers):
        res = client.get("/api/v1/auth/me", headers=admin_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "admin@test.com"
        assert data["role"] == "admin"

    def test_get_me_no_token(self, client):
        res = client.get("/api/v1/auth/me")
        assert res.status_code == 401


class TestUserList:

    def test_admin_can_list_users(self, client, admin_headers):
        res = client.get("/api/v1/auth/users", headers=admin_headers)
        assert res.status_code == 200
        data = res.json()
        assert "users" in data
        assert data["total"] >= 1

    def test_assistant_cannot_list_users(self, client, assistant_headers):
        res = client.get("/api/v1/auth/users", headers=assistant_headers)
        assert res.status_code == 403
