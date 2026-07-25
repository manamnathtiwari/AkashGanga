"""End-to-end API tests using the mock solver."""
import asyncio

import pytest


async def _register(client, email="star@example.com"):
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "display_name": "Star Gazer", "password": "supersecret"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_register_login_me(client):
    token = await _register(client, "me@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    me = await client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "me@example.com"

    login = await client.post(
        "/api/auth/login",
        json={"email": "me@example.com", "password": "supersecret"},
    )
    assert login.status_code == 200
    assert "access_token" in login.json()


@pytest.mark.asyncio
async def test_duplicate_registration_rejected(client):
    await _register(client, "dupe@example.com")
    resp = await client.post(
        "/api/auth/register",
        json={"email": "dupe@example.com", "display_name": "X", "password": "supersecret"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_requires_auth(client):
    assert (await client.get("/api/submissions")).status_code in (401, 403)


@pytest.mark.asyncio
async def test_url_submission_solves_and_annotates(client):
    token = await _register(client, "solve@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/submissions/url",
        json={"url": "http://example.com/andromeda.jpg", "options": {}},
        headers=headers,
    )
    assert resp.status_code == 202, resp.text
    sub_id = resp.json()["id"]

    # Background solve runs on the same loop; poll until finished.
    detail = None
    for _ in range(20):
        detail = (await client.get(f"/api/submissions/{sub_id}", headers=headers)).json()
        if detail["status"] in ("success", "failed"):
            break
        await asyncio.sleep(0.05)

    assert detail["status"] == "success"
    assert detail["ra"] == pytest.approx(170.0)
    names = {a["display_name"] for a in detail["annotations"]}
    assert "M 66" in names
    assert "NGC 3628" in names
    assert detail["objects_in_field"]
