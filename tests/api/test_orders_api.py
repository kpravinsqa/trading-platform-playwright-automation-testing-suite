import pytest
from jsonschema import validate

from api.schemas import ACCOUNT, INSTRUMENT, ORDER
from api.trading_client import TradingClient


@pytest.fixture
def client(api) -> TradingClient:
    return TradingClient(api)


@pytest.mark.api
@pytest.mark.smoke
def test_account_contract(client):
    resp = client.account()
    assert resp.ok
    body = resp.json()
    validate(body, ACCOUNT)
    assert body["total_value"] == pytest.approx(body["cash"] + body["invested"], abs=0.01)


@pytest.mark.api
@pytest.mark.regression
def test_instrument_contract(client):
    for item in client.search().json()["items"]:
        validate(item, INSTRUMENT)


@pytest.mark.api
@pytest.mark.smoke
def test_market_buy_contract_and_cash_movement(client):
    before = client.account().json()["cash"]
    resp = client.place(symbol="AMZN", side="BUY", order_type="MARKET", quantity=10)
    assert resp.status == 201
    order = resp.json()
    validate(order, ORDER)
    assert order["status"] == "FILLED"
    assert order["commission"] == 5.00
    after = client.account().json()["cash"]
    assert before - after == pytest.approx(10 * 178.40 + 5.00, abs=0.01)


@pytest.mark.api
@pytest.mark.regression
def test_average_price_recalculated_after_second_buy(client):
    client.place(symbol="AAPL", side="BUY", order_type="MARKET", quantity=10)
    pos = next(p for p in client.account().json()["positions"] if p["symbol"] == "AAPL")
    assert pos["quantity"] == 20
    assert pos["avg_price"] == pytest.approx((10 * 175.00 + 10 * 189.25) / 20, abs=0.0001)


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.parametrize("order, field, message", [
    ({"symbol": "AAPL", "side": "HOLD", "order_type": "MARKET", "quantity": 1}, "side", "Side must be BUY or SELL"),
    ({"symbol": "AAPL", "side": "BUY", "order_type": "STOP", "quantity": 1}, "order_type", "Order type must be MARKET or LIMIT"),
    ({"symbol": "AAPL", "side": "BUY", "order_type": "MARKET", "quantity": 1.5}, "quantity", "Quantity must be a whole number between 1 and 10,000"),
    ({"symbol": "AAPL", "side": "BUY", "order_type": "MARKET", "quantity": "10"}, "quantity", "Quantity must be a whole number between 1 and 10,000"),
    ({"symbol": "NOPE", "side": "BUY", "order_type": "MARKET", "quantity": 1}, "symbol", "Instrument not found"),
    ({"symbol": "AAPL", "side": "BUY", "order_type": "LIMIT", "quantity": 1}, "limit_price", "Limit price must be greater than zero"),
    ({"side": "BUY", "order_type": "MARKET", "quantity": 1}, "symbol", "Symbol is required"),
], ids=["bad-side", "bad-type", "fractional-qty", "string-qty", "unknown-symbol", "limit-no-price", "missing-symbol"])
def test_order_validation(client, order, field, message):
    resp = client.place(**order)
    assert resp.status in (400, 404)
    assert resp.json() == {"error": message, "field": field}


@pytest.mark.api
@pytest.mark.regression
def test_failed_order_does_not_change_cash(client):
    before = client.account().json()["cash"]
    assert client.place(symbol="NVDA", side="BUY", order_type="MARKET", quantity=9999).status == 422
    assert client.account().json()["cash"] == before


@pytest.mark.api
@pytest.mark.regression
def test_marketable_limit_fills_at_market_price(client):
    order = client.place(symbol="BP", side="BUY", order_type="LIMIT", quantity=100, limit_price=5.00).json()
    assert order["status"] == "FILLED"
    assert order["fill_price"] == 4.86


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
def test_cannot_cancel_filled_order(client):
    order = client.place(symbol="BP", side="BUY", order_type="MARKET", quantity=1).json()
    resp = client.cancel(order["id"])
    assert resp.status == 409
    assert "Only pending orders can be cancelled" in resp.json()["error"]


@pytest.mark.api
@pytest.mark.regression
def test_orders_are_isolated_per_user(client, playwright, base_url):
    client.place(symbol="BP", side="BUY", order_type="MARKET", quantity=1)
    other = playwright.request.new_context(base_url=base_url)
    token = other.post("/api/auth/login", data={"username": "low_balance", "password": "Trade@123"}).json()["token"]
    resp = other.get("/api/orders", headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["count"] == 0
    other.dispose()
