import pytest

from api.trading_client import TradingClient


@pytest.fixture
def client(api) -> TradingClient:
    return TradingClient(api)


@pytest.mark.api
@pytest.mark.smoke
def test_watchlist_crud_lifecycle(client):
    created = client.create_watchlist("Dividend Picks")
    assert created.status == 201
    wid = created.json()["id"]
    assert client.add_symbol(wid, "ulvr").json()["symbols"] == ["ULVR"]
    assert client.add_symbol(wid, "GSK").status == 201
    assert client.remove_symbols(wid, ["ULVR"]).json()["symbols"] == ["GSK"]
    assert client.delete_watchlist(wid).json() == {"deleted": wid}
    assert all(w["id"] != wid for w in client.watchlists().json()["items"])


@pytest.mark.api
@pytest.mark.regression
def test_max_ten_watchlists(client):
    for i in range(9):
        assert client.create_watchlist(f"List {i}").status == 201
    resp = client.create_watchlist("One Too Many")
    assert resp.status == 400
    assert resp.json()["error"] == "You can create a maximum of 10 watchlists"


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
def test_remove_with_empty_selection_is_rejected(client):
    wid = client.watchlists().json()["items"][0]["id"]
    resp = client.remove_symbols(wid, [])
    assert resp.status == 400
    assert resp.json()["field"] == "symbols"


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
def test_unknown_watchlist_returns_404(client):
    assert client.delete_watchlist(999999).status == 404
