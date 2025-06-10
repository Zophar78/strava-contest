# pylint: disable=redefined-outer-name
import pytest
from contest.models import User

@pytest.fixture
def admin_credentials(app_fixture):
    return {
        "email": app_fixture.config["ADMIN_EMAIL"],
        "password": app_fixture.config["ADMIN_PASSWORD"]
    }

def test_admin_access(client, admin_credentials):
    client.post("/login", data=admin_credentials, follow_redirects=True)
    response = client.get("/admin")
    assert response.status_code == 200
    assert b"Admin Dashboard" in response.data

def test_non_admin_forbidden(client, db_session):
    user = User(email="user@test.com", is_admin=False)
    user.set_password("user")
    db_session.add(user)
    db_session.commit()
    client.post("/login", data={"email": "user@test.com", "password": "user"}, follow_redirects=True)
    response = client.get("/admin")
    assert response.status_code == 403

def test_anonymous_forbidden(client):
    response = client.get("/admin")
    assert response.status_code in (302, 403)

def test_admin_dashboard_access(client, admin_credentials):
    client.post("/login", data=admin_credentials, follow_redirects=True)
    resp = client.get("/admin")
    assert resp.status_code == 200
    assert b"Admin Dashboard" in resp.data

def test_admin_settings_access(client, admin_credentials):
    client.post("/login", data=admin_credentials, follow_redirects=True)
    resp = client.get("/admin/settings")
    assert resp.status_code == 200
    assert b"Site Settings" in resp.data

def test_admin_settings_post_theme(client, admin_credentials):
    client.post("/login", data=admin_credentials, follow_redirects=True)
    resp = client.post(
        "/admin/settings",
        data={'theme': 'darkly', 'primary_color': '#123456', 'dashboard_title': 'Test Dashboard'},
        follow_redirects=True
    )
    assert resp.status_code == 200
    assert b"Settings updated" in resp.data
