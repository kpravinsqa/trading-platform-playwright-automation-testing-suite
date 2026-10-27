"""Thin service-object wrapper over Playwright's APIRequestContext."""
from playwright.sync_api import APIRequestContext, APIResponse


class TradingClient:
    def __init__(self, ctx: APIRequestContext):
        self.ctx = ctx

    # account / instruments
    def account(self) -> APIResponse:
        return self.ctx.get("/api/account")

    def search(self, q: str = "") -> APIResponse:
        return self.ctx.get("/api/instruments", params={"q": q})

    # watchlists
    def watchlists(self) -> APIResponse:
        return self.ctx.get("/api/watchlists")

    def create_watchlist(self, name: str) -> APIResponse:
        return self.ctx.post("/api/watchlists", data={"name": name})

    def delete_watchlist(self, wid: int) -> APIResponse:
        return self.ctx.delete(f"/api/watchlists/{wid}")

    def add_symbol(self, wid: int, symbol: str) -> APIResponse:
        return self.ctx.post(f"/api/watchlists/{wid}/symbols", data={"symbol": symbol})

    def remove_symbols(self, wid: int, symbols: list[str]) -> APIResponse:
        return self.ctx.post(f"/api/watchlists/{wid}/symbols/remove", data={"symbols": symbols})

    # orders
    def preview(self, **order) -> APIResponse:
        return self.ctx.post("/api/orders/preview", data=order)

    def place(self, **order) -> APIResponse:
        return self.ctx.post("/api/orders", data=order)

    def orders(self, status: str | None = None) -> APIResponse:
        return self.ctx.get("/api/orders", params={"status": status} if status else None)

    def cancel(self, order_id: int) -> APIResponse:
        return self.ctx.post(f"/api/orders/{order_id}/cancel")
