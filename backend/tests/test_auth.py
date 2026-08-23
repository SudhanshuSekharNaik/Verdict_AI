import pytest
import uuid


@pytest.mark.asyncio
async def test_auth_registration_and_login(async_client):
    test_email = f"advocate_{uuid.uuid4().hex[:6]}@aadalat.ai"
    reg_payload = {
        "email": test_email,
        "password": "SecurePassword123!",
        "full_name": "Advocate Test Sharma",
        "role": "USER",
    }
    # Register
    reg_res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["success"] is True
    assert reg_data["data"]["email"] == test_email

    # Login
    login_payload = {
        "email": test_email,
        "password": "SecurePassword123!",
    }
    login_res = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert token_data["success"] is True
    token = token_data["data"]["access_token"]
    assert token is not None

    # Get Me
    me_res = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == test_email
