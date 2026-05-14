import uuid
import pytest


@pytest.mark.asyncio
async def test_register_user(client):
    payload = {
        "name": "Divyansh",
        "age": 22,
        "email": f"{uuid.uuid4()}@test.com",
        "password": "password123",
        "role": "candidate"
    }

    response = await client.post(
        "/users",
        json=payload
    )

    assert response.status_code in [200, 201]

    data = response.json()

    assert data["email"] == payload["email"]
    assert data["name"] == payload["name"]


@pytest.mark.asyncio
async def test_login_user(client):
    email = f"{uuid.uuid4()}@test.com"

    register_payload = {
        "name": "Divyansh",
        "age": 22,
        "email": email,
        "password": "password123",
        "role": "candidate"
    }

    await client.post(
        "/users",
        json=register_payload
    )

    login_payload = {
        "email": email,
        "password": "password123"
    }

    response = await client.post(
        "/login",
        json=login_payload
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data


@pytest.mark.asyncio
async def test_invalid_login(client):
    payload = {
        "email": "wrong@test.com",
        "password": "wrongpassword"
    }

    response = await client.post(
        "/login",
        json=payload
    )

    assert response.status_code in [400, 401]


@pytest.mark.asyncio
async def test_get_jobs(client):
    response = await client.get("/jobs/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)