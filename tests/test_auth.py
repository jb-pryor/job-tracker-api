from sqlalchemy import select

from app.models import User
from app.security import verify_password


def test_registration_saves_hashed_password(client, db_session):
    response = client.post(
        "/auth/register",
        json={
            "email": "  TEST@EXAMPLE.COM  ",
            "password": "a-long-test-password",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "test@example.com"
    assert isinstance(data["id"], int)
    assert "created_at" in data
    assert "password" not in data
    assert "password_hash" not in data

    user = db_session.scalar(
        select(User).where(User.email == "test@example.com")
    )

    assert user is not None
    assert user.password_hash != "a-long-test-password"
    assert verify_password("a-long-test-password", user.password_hash)


def test_duplicate_email_returns_conflict(client):
    registration = {
        "email": "duplicate@example.com",
        "password": "a-long-test-password",
    }

    first_response = client.post("/auth/register", json=registration)
    second_response = client.post("/auth/register", json=registration)

    assert first_response.status_code == 201
    assert second_response.status_code == 409

    # Verify the session remains usable after the failed transaction.
    third_response = client.post(
        "/auth/register",
        json={
            "email": "different@example.com",
            "password": "a-long-test-password",
        },
    )

    assert third_response.status_code == 201


def test_login_returns_access_token(client):
    email = "login@example.com"
    password = "a-long-practice-password"

    registration = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert registration.status_code == 201

    response = client.post(
        "/auth/token",
        data={"username": email, "password": password},
    )

    assert response.status_code == 200

    token = response.json()
    assert token["token_type"] == "bearer"
    assert isinstance(token["access_token"], str)
    assert token["access_token"]

    # Verify that the issued token actually authenticates this user.
    profile = client.get(
        "/users/me",
        headers={
            "Authorization": f"Bearer {token['access_token']}"
        },
    )

    assert profile.status_code == 200
    assert profile.json()["id"] == registration.json()["id"]
    assert profile.json()["email"] == email


def test_login_rejects_wrong_password(client):
    email = "wrong-password@example.com"

    registration = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "a-long-practice-password",
        },
    )
    assert registration.status_code == 201

    response = client.post(
        "/auth/token",
        data={
            "username": email,
            "password": "an-incorrect-password",
        },
    )

    assert response.status_code == 401
    assert "access_token" not in response.json()


def test_current_user_requires_token(client):
    response = client.get("/users/me")

    assert response.status_code == 401


def test_current_user_rejects_invalid_token(client):
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401