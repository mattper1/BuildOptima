import pytest
from core.security import hash_password
from models.user import User
from models.build import Build

SAMPLE_BUILD = {
    "build_name": "My Gaming Rig",
    "use_case": "gaming",
    "budget": 1500,
    "total_price": 1423.0,
    "components": [
        {
            "category": "cpu",
            "part_name": "Ryzen 5 7600X",
            "part_price": 229.0,
            "reason_selected": "Great gaming CPU",
        }
    ],
}


@pytest.fixture
def auth_headers(client):
    client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    res = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_save_build_returns_201_with_components(client, auth_headers):
    res = client.post("/builds/save", json=SAMPLE_BUILD, headers=auth_headers)
    assert res.status_code == 201
    body = res.json()
    assert body["build_name"] == "My Gaming Rig"
    assert len(body["components"]) == 1
    assert body["components"][0]["part_name"] == "Ryzen 5 7600X"


def test_save_build_without_auth_returns_401(client):
    res = client.post("/builds/save", json=SAMPLE_BUILD)
    assert res.status_code == 401


def test_list_builds_returns_only_current_user_builds(client, auth_headers, db):
    client.post("/builds/save", json=SAMPLE_BUILD, headers=auth_headers)
    # Another user's build — inserted directly
    other = User(email="other@example.com", hashed_password=hash_password("pass1234"))
    db.add(other)
    db.flush()
    db.add(
        Build(
            user_id=other.id,
            build_name="Other Build",
            use_case="gaming",
            budget=1000,
            total_price=900.0,
        )
    )
    db.commit()
    res = client.get("/builds", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["build_name"] == "My Gaming Rig"


def test_get_build_returns_components(client, auth_headers):
    saved = client.post(
        "/builds/save", json=SAMPLE_BUILD, headers=auth_headers
    ).json()
    res = client.get(f"/builds/{saved['id']}", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()["components"]) == 1


def test_get_build_other_users_build_returns_403(client, auth_headers, db):
    other = User(email="other@example.com", hashed_password=hash_password("pass1234"))
    db.add(other)
    db.flush()
    build = Build(
        user_id=other.id,
        build_name="Other Build",
        use_case="gaming",
        budget=1000,
        total_price=900.0,
    )
    db.add(build)
    db.commit()
    res = client.get(f"/builds/{build.id}", headers=auth_headers)
    assert res.status_code == 403


def test_get_build_not_found_returns_404(client, auth_headers):
    res = client.get("/builds/9999", headers=auth_headers)
    assert res.status_code == 404


def test_delete_build_returns_204(client, auth_headers):
    saved = client.post(
        "/builds/save", json=SAMPLE_BUILD, headers=auth_headers
    ).json()
    res = client.delete(f"/builds/{saved['id']}", headers=auth_headers)
    assert res.status_code == 204
    assert client.get(f"/builds/{saved['id']}", headers=auth_headers).status_code == 404


def test_delete_other_users_build_returns_403(client, auth_headers, db):
    other = User(email="other@example.com", hashed_password=hash_password("pass1234"))
    db.add(other)
    db.flush()
    build = Build(
        user_id=other.id,
        build_name="Other Build",
        use_case="gaming",
        budget=1000,
        total_price=900.0,
    )
    db.add(build)
    db.commit()
    res = client.delete(f"/builds/{build.id}", headers=auth_headers)
    assert res.status_code == 403
