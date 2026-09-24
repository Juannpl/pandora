import jwt
import pytest

from core.config import SECRET_KEY
from core.security import ALGORITHM

USER = {
    "first_name": "Alex",
    "last_name": "Martin",
    "email": "alex@example.com",
    "password": "test-password-123",
}


async def register(client):
    response = await client.post("/api/v1/users/", json=USER)
    assert response.status_code == 200, response.text
    return response.json()


async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


async def test_user_crud(client):
    created = await register(client)
    user_id = created["id"]
    assert created["email"] == USER["email"]
    response = await client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["first_name"] == "Alex"
    response = await client.get("/api/v1/users/")
    assert response.status_code == 200
    assert [user["id"] for user in response.json()] == [user_id]
    response = await client.put(
        f"/api/v1/users/{user_id}",
        json={"first_name": "Sam", "last_name": "Durand"},
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "Sam"
    assert response.json()["last_name"] == "Durand"
    response = await client.get(f"/api/v1/users/{user_id}")
    assert response.json()["first_name"] == "Sam"
    response = await client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    assert (await client.get(f"/api/v1/users/{user_id}")).status_code == 404
    assert (await client.get("/api/v1/users/")).json() == []


async def test_duplicate_email(client):
    await register(client)
    response = await client.post("/api/v1/users/", json=USER)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.parametrize("changes", [{"email": "invalid"}, {"password": "short"}])
async def test_invalid_registration(client, changes):
    response = await client.post("/api/v1/users/", json={**USER, **changes})
    assert response.status_code == 422
    assert (await client.get("/api/v1/users/")).json() == []


@pytest.mark.parametrize("method", ["get", "put", "delete"])
async def test_missing_user(client, method):
    kwargs = {"json": {"first_name": "Alex", "last_name": "Martin"}} if method == "put" else {}
    response = await getattr(client, method)("/api/v1/users/99999", **kwargs)
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


async def test_authentication_and_password_change(client):
    created = await register(client)
    credentials = {"email": USER["email"], "password": USER["password"]}
    response = await client.post("/api/v1/auth", json=credentials)
    assert response.status_code == 200
    payload = jwt.decode(response.json()["data"], SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == USER["email"]
    response = await client.put(
        f'/api/v1/users/{created["id"]}',
        json={"first_name": "Alex", "last_name": "Martin", "password": "new-password-456"},
    )
    assert response.status_code == 200
    assert (await client.post("/api/v1/auth", json=credentials)).status_code == 401
    response = await client.post(
        "/api/v1/auth", json={**credentials, "password": "new-password-456"}
    )
    assert response.status_code == 200


@pytest.mark.parametrize("email,password", [
    ("alex@example.com", "incorrect-password"),
    ("unknown@example.com", "test-password-123"),
])
async def test_invalid_credentials(client, email, password):
    await register(client)
    response = await client.post("/api/v1/auth", json={"email": email, "password": password})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
