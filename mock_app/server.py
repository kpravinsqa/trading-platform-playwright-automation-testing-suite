"""
Mock "share-dealing" web platform (investment / brokerage domain).

Synthetic re-creation of the business rules exercised while testing an
equity investing platform: authentication, instrument search, watchlists,
order placement (market / limit), commission calculation, positions and
order history. No proprietary code or data is used.
"""
from __future__ import annotations

import copy
import itertools
from datetime import datetime, timezone
from pathlib import Path

from mock_app.core import ApiError, App, require

app = App(Path(__file__).parent / "static")

CURRENCY = "GBP"
MIN_COMMISSION = 5.00
COMMISSION_RATE = 0.001          # 0.10 % of notional, minimum £5
MAX_QTY = 10_000
MAX_WATCHLISTS = 10
WATCHLIST_NAME_MAX = 30
MAX_FAILED_LOGINS = 3

USERS_SEED = {
    "demo_trader": {"password": "Trade@123", "display_name": "Demo Trader", "status": "ACTIVE", "cash": 25_000.00},
    "low_balance": {"password": "Trade@123", "display_name": "Low Balance", "status": "ACTIVE", "cash": 150.00},
    "locked_user": {"password": "Trade@123", "display_name": "Locked User", "status": "LOCKED", "cash": 0.0},
}

INSTRUMENTS_SEED = [
    {"symbol": "AAPL", "name": "Apple Inc", "exchange": "NASDAQ", "price": 189.25, "status": "OPEN"},
    {"symbol": "MSFT", "name": "Microsoft Corp", "exchange": "NASDAQ", "price": 412.10, "status": "OPEN"},
    {"symbol": "AMZN", "name": "Amazon.com Inc", "exchange": "NASDAQ", "price": 178.40, "status": "OPEN"},
    {"symbol": "TSLA", "name": "Tesla Inc", "exchange": "NASDAQ", "price": 248.50, "status": "OPEN"},
    {"symbol": "NVDA", "name": "NVIDIA Corp", "exchange": "NASDAQ", "price": 121.75, "status": "OPEN"},
    {"symbol": "VOD", "name": "Vodafone Group", "exchange": "LSE", "price": 0.72, "status": "OPEN"},
    {"symbol": "BP", "name": "BP plc", "exchange": "LSE", "price": 4.86, "status": "OPEN"},
    {"symbol": "HSBA", "name": "HSBC Holdings", "exchange": "LSE", "price": 6.95, "status": "OPEN"},
    {"symbol": "BARC", "name": "Barclays plc", "exchange": "LSE", "price": 2.31, "status": "OPEN"},
    {"symbol": "ULVR", "name": "Unilever plc", "exchange": "LSE", "price": 44.20, "status": "OPEN"},
    {"symbol": "GSK", "name": "GSK plc", "exchange": "LSE", "price": 15.60, "status": "OPEN"},
    {"symbol": "HALT", "name": "Halted Mining Co", "exchange": "LSE", "price": 1.10, "status": "SUSPENDED"},
]

STATE: dict = {}
_ids = itertools.count(1)


def reset() -> None:
    global _ids
    _ids = itertools.count(1001)
    app.revoke_all_tokens()
    STATE.clear()
    STATE["users"] = copy.deepcopy(USERS_SEED)
    STATE["failed"] = {}
    STATE["instruments"] = {i["symbol"]: dict(i) for i in INSTRUMENTS_SEED}
    STATE["positions"] = {u: {} for u in USERS_SEED}
    STATE["positions"]["demo_trader"] = {"AAPL": {"quantity": 10, "avg_price": 175.00}}
    STATE["orders"] = {u: [] for u in USERS_SEED}
    STATE["watchlists"] = {
        u: [{"id": next(_ids), "name": "My Watchlist", "default": True, "symbols": ["AAPL", "MSFT"]}]
        for u in USERS_SEED
    }


def commission_for(notional: float) -> float:
    return round(max(MIN_COMMISSION, notional * COMMISSION_RATE), 2)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------- test hooks
@app.route("POST", "/api/test/reset", auth=False)
def _reset(req):
    reset()
    return {"status": "reset"}


# --------------------------------------------------------------------------- auth
@app.route("POST", "/api/auth/login", auth=False)
def login(req):
    username = require(req.body, "username", "Username")
    password = require(req.body, "password", "Password", strip=False)
    user = STATE["users"].get(username)
    if user and user["status"] == "LOCKED":
        raise ApiError(423, "Account locked. Please contact support.")
    if not user or user["password"] != password:
        if user:
            STATE["failed"][username] = STATE["failed"].get(username, 0) + 1
            if STATE["failed"][username] >= MAX_FAILED_LOGINS:
                user["status"] = "LOCKED"
                raise ApiError(423, "Account locked. Please contact support.")
        raise ApiError(401, "Invalid username or password")
    STATE["failed"][username] = 0
    profile = {"username": username, "display_name": user["display_name"]}
    return {"token": app.issue_token(profile), "user": profile}


# --------------------------------------------------------------------------- account
@app.route("GET", "/api/account")
def account(req):
    username = req.user["username"]
    cash = STATE["users"][username]["cash"]
    positions = []
    for sym, pos in STATE["positions"][username].items():
        price = STATE["instruments"][sym]["price"]
        mv = round(pos["quantity"] * price, 2)
        positions.append({
            "symbol": sym, "quantity": pos["quantity"], "avg_price": round(pos["avg_price"], 4),
            "last_price": price, "market_value": mv,
            "unrealised_pnl": round(mv - pos["quantity"] * pos["avg_price"], 2),
        })
    invested = round(sum(p["market_value"] for p in positions), 2)
    return {"currency": CURRENCY, "cash": round(cash, 2), "invested": invested,
            "total_value": round(cash + invested, 2), "positions": positions}


# --------------------------------------------------------------------------- instruments
@app.route("GET", "/api/instruments")
def instruments(req):
    q = (req.query.get("q") or "").strip().lower()
    items = [i for i in STATE["instruments"].values()
             if not q or q in i["symbol"].lower() or q in i["name"].lower()]
    return {"count": len(items), "items": items}


@app.route("GET", r"/api/instruments/(?P<symbol>[A-Za-z]+)")
def instrument(req):
    item = STATE["instruments"].get(req.params["symbol"].upper())
    if not item:
        raise ApiError(404, "Instrument not found")
    return item


# --------------------------------------------------------------------------- watchlists
def _watchlists(req):
    return STATE["watchlists"][req.user["username"]]


def _find_watchlist(req):
    wid = int(req.params["wid"])
    for wl in _watchlists(req):
        if wl["id"] == wid:
            return wl
    raise ApiError(404, "Watchlist not found")


def _validate_name(req, name, exclude_id=None):
    if len(name) > WATCHLIST_NAME_MAX:
        raise ApiError(400, f"Name must be {WATCHLIST_NAME_MAX} characters or fewer", field="name")
    if any(w["name"].lower() == name.lower() and w["id"] != exclude_id for w in _watchlists(req)):
        raise ApiError(409, "A watchlist with this name already exists", field="name")


@app.route("GET", "/api/watchlists")
def list_watchlists(req):
    return {"items": _watchlists(req)}


@app.route("POST", "/api/watchlists")
def create_watchlist(req):
    name = require(req.body, "name", "Watchlist name")
    if len(_watchlists(req)) >= MAX_WATCHLISTS:
        raise ApiError(400, f"You can create a maximum of {MAX_WATCHLISTS} watchlists")
    _validate_name(req, name)
    wl = {"id": next(_ids), "name": name, "default": False, "symbols": []}
    _watchlists(req).append(wl)
    return 201, wl


@app.route("PUT", r"/api/watchlists/(?P<wid>\d+)")
def rename_watchlist(req):
    wl = _find_watchlist(req)
    name = require(req.body, "name", "Watchlist name")
    _validate_name(req, name, exclude_id=wl["id"])
    wl["name"] = name
    return wl


@app.route("DELETE", r"/api/watchlists/(?P<wid>\d+)")
def delete_watchlist(req):
    wl = _find_watchlist(req)
    if wl["default"]:
        raise ApiError(400, "The default watchlist cannot be deleted")
    _watchlists(req).remove(wl)
    return {"deleted": wl["id"]}


@app.route("POST", r"/api/watchlists/(?P<wid>\d+)/symbols")
def add_symbol(req):
    wl = _find_watchlist(req)
    symbol = require(req.body, "symbol", "Symbol").upper()
    if symbol not in STATE["instruments"]:
        raise ApiError(404, "Instrument not found", field="symbol")
    if symbol in wl["symbols"]:
        raise ApiError(409, f"{symbol} is already in this watchlist")
    wl["symbols"].append(symbol)
    return 201, wl


@app.route("POST", r"/api/watchlists/(?P<wid>\d+)/symbols/remove")
def remove_symbols(req):
    """Bulk-remove the *selected* symbols only (guards a real selection/deletion defect)."""
    wl = _find_watchlist(req)
    symbols = [s.upper() for s in req.body.get("symbols") or []]
    if not symbols:
        raise ApiError(400, "Select at least one instrument to remove", field="symbols")
    wl["symbols"] = [s for s in wl["symbols"] if s not in symbols]
    return wl


# --------------------------------------------------------------------------- orders
def _parse_order(body):
    symbol = require(body, "symbol", "Symbol").upper()
    side = require(body, "side", "Side").upper()
    order_type = require(body, "order_type", "Order type").upper()
    if side not in ("BUY", "SELL"):
        raise ApiError(400, "Side must be BUY or SELL", field="side")
    if order_type not in ("MARKET", "LIMIT"):
        raise ApiError(400, "Order type must be MARKET or LIMIT", field="order_type")
    qty = body.get("quantity")
    if not isinstance(qty, int) or isinstance(qty, bool) or qty < 1 or qty > MAX_QTY:
        raise ApiError(400, f"Quantity must be a whole number between 1 and {MAX_QTY:,}", field="quantity")
    instrument = STATE["instruments"].get(symbol)
    if not instrument:
        raise ApiError(404, "Instrument not found", field="symbol")
    if instrument["status"] != "OPEN":
        raise ApiError(422, "Instrument is suspended from trading", field="symbol")
    limit_price = body.get("limit_price")
    if order_type == "LIMIT":
        if not isinstance(limit_price, (int, float)) or limit_price <= 0:
            raise ApiError(400, "Limit price must be greater than zero", field="limit_price")
    else:
        limit_price = None
    return symbol, side, order_type, qty, instrument, limit_price


def _quote(side, qty, price):
    notional = round(qty * price, 2)
    commission = commission_for(notional)
    total = round(notional + commission, 2) if side == "BUY" else round(notional - commission, 2)
    return {"notional": notional, "commission": commission, "estimated_total": total}


@app.route("POST", "/api/orders/preview")
def preview(req):
    symbol, side, order_type, qty, instrument, limit_price = _parse_order(req.body)
    price = limit_price or instrument["price"]
    return {"symbol": symbol, "side": side, "quantity": qty, "price": price, "currency": CURRENCY,
            **_quote(side, qty, price)}


def _execute(username, order):
    pos_book = STATE["positions"][username]
    q = _quote(order["side"], order["quantity"], order["fill_price"])
    if order["side"] == "BUY":
        STATE["users"][username]["cash"] -= q["estimated_total"]
        pos = pos_book.setdefault(order["symbol"], {"quantity": 0, "avg_price": 0.0})
        new_qty = pos["quantity"] + order["quantity"]
        pos["avg_price"] = (pos["quantity"] * pos["avg_price"] + order["quantity"] * order["fill_price"]) / new_qty
        pos["quantity"] = new_qty
    else:
        STATE["users"][username]["cash"] += q["estimated_total"]
        pos = pos_book[order["symbol"]]
        pos["quantity"] -= order["quantity"]
        if pos["quantity"] == 0:
            del pos_book[order["symbol"]]
    order.update(status="FILLED", commission=q["commission"], total=q["estimated_total"], filled_at=now())


@app.route("POST", "/api/orders")
def place_order(req):
    username = req.user["username"]
    symbol, side, order_type, qty, instrument, limit_price = _parse_order(req.body)
    market = instrument["price"]
    check_price = limit_price if order_type == "LIMIT" else market
    q = _quote(side, qty, check_price)
    if side == "BUY" and q["estimated_total"] > STATE["users"][username]["cash"]:
        raise ApiError(422, "Insufficient funds for this order", field="quantity")
    held = STATE["positions"][username].get(symbol, {}).get("quantity", 0)
    if side == "SELL" and qty > held:
        raise ApiError(422, f"Insufficient holdings: you hold {held} {symbol}", field="quantity")

    order = {"id": next(_ids), "symbol": symbol, "side": side, "order_type": order_type, "quantity": qty,
             "limit_price": limit_price, "status": "PENDING", "created_at": now(), "currency": CURRENCY}
    marketable = order_type == "MARKET" or (side == "BUY" and limit_price >= market) or \
        (side == "SELL" and limit_price <= market)
    if marketable:
        order["fill_price"] = market
        _execute(username, order)
    STATE["orders"][username].insert(0, order)
    return 201, order


@app.route("GET", "/api/orders")
def list_orders(req):
    items = STATE["orders"][req.user["username"]]
    status = req.query.get("status")
    if status:
        items = [o for o in items if o["status"] == status.upper()]
    return {"count": len(items), "items": items}


@app.route("POST", r"/api/orders/(?P<oid>\d+)/cancel")
def cancel_order(req):
    for order in STATE["orders"][req.user["username"]]:
        if order["id"] == int(req.params["oid"]):
            if order["status"] != "PENDING":
                raise ApiError(409, f"Only pending orders can be cancelled (status: {order['status']})")
            order["status"] = "CANCELLED"
            return order
    raise ApiError(404, "Order not found")


def create_server(host: str = "127.0.0.1", port: int = 0):
    reset()
    return app.create_server(host, port)


if __name__ == "__main__":
    srv = create_server("127.0.0.1", 8000)
    print("Mock trading platform running at http://127.0.0.1:8000  (demo_trader / Trade@123)")
    srv.serve_forever()
