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