import pytest

from config.settings import settings


@pytest.mark.api
@pytest.mark.smoke
def test_login_returns_token(anon_api):
    resp = anon_api.post("/api/auth/login", data=settings.default_credentials)
    assert resp.status == 200
    body = resp.json()
    assert len(body["token"]) == 32
    assert body["user"] == {"username": "demo_trader", "display_name": "Demo Trader"}


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.parametrize("payload, status, error", [
    ({"username": "demo_trader", "password": "nope"}, 401, "Invalid username or password"),
    ({"username": "demo_trader"}, 400, "Password is required"),
    ({"password": "Trade@123"}, 400, "Username is required"),
    ({"username": "locked_user", "password": "Trade@123"}, 423, "Account locked. Please contact support."),
], ids=["bad-password", "missing-password", "missing-username", "locked"])
def test_login_errors(anon_api, payload, status, error):
    resp = anon_api.post("/api/auth/login", data=payload)
    assert resp.status == status
    assert resp.json()["error"] == error


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.parametrize("endpoint", ["/api/account", "/api/orders", "/api/watchlists", "/api/instruments"])
def test_protected_endpoints_require_token(anon_api, endpoint):
    resp = anon_api.get(endpoint)
    assert resp.status == 401
    assert resp.json() == {"error": "Authentication required"}


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
def test_forged_token_rejected(anon_api):
    resp = anon_api.get("/api/account", headers={"Authorization": "Bearer " + "f" * 32})
    assert resp.status == 401
