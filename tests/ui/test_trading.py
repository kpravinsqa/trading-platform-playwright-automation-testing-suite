"""Order placement — maps to manual suite TS-04 (Order Ticket) and TS-05 (Orders & Positions)."""
import re

import pytest
from playwright.sync_api import Page, expect

from config.settings import settings
from pages.dashboard_page import DashboardPage
from pages.orders_page import OrdersPage
from pages.trade_page import TradePage
from utils.data_loader import cases


@pytest.fixture
def trade(logged_in_page: Page) -> TradePage:
    return TradePage(logged_in_page).open()


@pytest.mark.ui
@pytest.mark.smoke
def test_market_buy_fills_and_updates_portfolio(logged_in_page: Page, trade: TradePage):
    trade.fill_order("MSFT", "BUY", "MARKET", quantity=5)
    trade.place()
    expect(trade.confirm_status).to_have_text("FILLED")

    dashboard = DashboardPage(logged_in_page).open()
    expected_cash = 25_000 - (5 * 412.10 + settings.min_commission)
    assert dashboard.cash_value() == pytest.approx(expected_cash, abs=0.01)
    assert dashboard.position_qty("MSFT") == 5


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("case", cases("orders", "commission"))
def test_order_preview_commission(trade: TradePage, case):
    trade.fill_order(case["symbol"], "BUY", "MARKET", quantity=case["quantity"])
    trade.preview()
    expect(trade.preview_panel).to_be_visible()
    expect(trade.preview_notional).to_have_text(f"£{case['expected_notional']:.2f}")
    expect(trade.preview_commission).to_have_text(f"£{case['expected_commission']:.2f}")
    total = case["expected_notional"] + case["expected_commission"]
    expect(trade.preview_total).to_have_text(f"£{total:.2f}")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("case", cases("orders", "quantity_boundaries"))
def test_quantity_boundary_values(trade: TradePage, case):
    trade.fill_order("VOD", "BUY", "MARKET", quantity=case["quantity"])
    trade.preview()
    if case["valid"]:
        expect(trade.preview_panel).to_be_visible()
        expect(trade.field_error("quantity")).to_have_text("")
    else:
        expect(trade.field_error("quantity")).to_have_text("Quantity must be a whole number between 1 and 10,000")
        expect(trade.preview_panel).to_be_hidden()


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
def test_insufficient_funds_is_blocked(trade: TradePage):
    trade.fill_order("NVDA", "BUY", "MARKET", quantity=500)
    trade.place()
    expect(trade.field_error("quantity")).to_have_text("Insufficient funds for this order")
    expect(trade.confirmation).to_be_hidden()


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
def test_cannot_sell_more_than_held(trade: TradePage):
    trade.fill_order("AAPL", "SELL", "MARKET", quantity=11)
    trade.place()
    expect(trade.field_error("quantity")).to_have_text("Insufficient holdings: you hold 10 AAPL")


@pytest.mark.ui
@pytest.mark.regression
def test_sell_entire_position_closes_it(logged_in_page: Page, trade: TradePage):
    trade.fill_order("AAPL", "SELL", "MARKET", quantity=10)
    trade.place()
    expect(trade.confirm_status).to_have_text("FILLED")
    dashboard = DashboardPage(logged_in_page).open()
    dashboard.cash_value()
    expect(dashboard.position_row("AAPL")).to_have_count(0)


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
def test_suspended_instrument_rejects_orders(trade: TradePage):
    trade.fill_order("HALT", "BUY", "MARKET", quantity=10)
    trade.place()
    expect(trade.field_error("symbol")).to_have_text("Instrument is suspended from trading")


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
def test_limit_order_requires_positive_price(trade: TradePage):
    trade.fill_order("BP", "BUY", "LIMIT", quantity=10, limit_price=0)
    trade.place()
    expect(trade.field_error("limit_price")).to_have_text("Limit price must be greater than zero")


@pytest.mark.ui
@pytest.mark.regression
def test_limit_price_field_enabled_only_for_limit_orders(trade: TradePage):
    expect(trade.limit_price).to_be_disabled()
    trade.order_type.select_option("LIMIT")
    expect(trade.limit_price).to_be_enabled()


@pytest.mark.ui
@pytest.mark.smoke
def test_non_marketable_limit_order_rests_then_cancel(logged_in_page: Page, trade: TradePage):
    trade.fill_order("TSLA", "BUY", "LIMIT", quantity=2, limit_price=200.00)
    trade.place()
    expect(trade.confirm_status).to_have_text("PENDING")
    order_id = int(re.sub(r"\D", "", trade.confirm_id.inner_text()))

    orders = OrdersPage(logged_in_page).open()
    expect(orders.status_of(order_id)).to_have_text("PENDING")
    orders.cancel(order_id)
    orders.expect_toast("Order cancelled")
    expect(orders.status_of(order_id)).to_have_text("CANCELLED")


@pytest.mark.ui
@pytest.mark.regression
def test_order_history_filter(logged_in_page: Page, api):
    api.post("/api/orders", data={"symbol": "BP", "side": "BUY", "order_type": "MARKET", "quantity": 10})
    api.post("/api/orders", data={"symbol": "BP", "side": "BUY", "order_type": "LIMIT", "quantity": 10, "limit_price": 1.0})
    orders = OrdersPage(logged_in_page).open()
    expect(orders.rows).to_have_count(2)
    orders.filter_by("PENDING")
    expect(orders.rows).to_have_count(1)
    orders.filter_by("CANCELLED")
    expect(orders.empty_state).to_be_visible()
