"""Instrument search — maps to manual suite TS-02 (Markets & Search)."""
import pytest
from playwright.sync_api import Page, expect

from pages.markets_page import MarketsPage
from pages.trade_page import TradePage
from pages.watchlist_page import WatchlistPage


@pytest.mark.ui
@pytest.mark.smoke
def test_search_by_symbol(logged_in_page: Page):
    markets = MarketsPage(logged_in_page).open()
    markets.search("TSLA")
    expect(markets.rows).to_have_count(1)
    expect(markets.row("TSLA")).to_contain_text("Tesla Inc")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("term, expected", [("apple", ["AAPL"]), ("plc", ["BP", "BARC", "ULVR", "GSK"]), ("ms", ["MSFT"])])
def test_search_is_case_insensitive_and_matches_name(logged_in_page: Page, term, expected):
    markets = MarketsPage(logged_in_page).open()
    markets.search(term)
    expect(markets.rows).to_have_count(len(expected))
    for symbol in expected:
        expect(markets.row(symbol)).to_be_visible()


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
def test_search_with_no_matches_shows_empty_state(logged_in_page: Page):
    markets = MarketsPage(logged_in_page).open()
    markets.search("ZZZNOTREAL")
    expect(markets.rows).to_have_count(0)
    expect(markets.no_results).to_be_visible()
    expect(markets.result_count).to_have_text("0 instrument(s) found")


@pytest.mark.ui
@pytest.mark.regression
def test_suspended_instrument_is_flagged(logged_in_page: Page):
    markets = MarketsPage(logged_in_page).open()
    markets.search("HALT")
    expect(markets.row("HALT").get_by_test_id("status")).to_have_text("SUSPENDED")


@pytest.mark.ui
@pytest.mark.regression
def test_add_instrument_to_default_watchlist_from_markets(logged_in_page: Page):
    markets = MarketsPage(logged_in_page).open()
    markets.search("NVDA")
    markets.add_to_watchlist("NVDA")
    markets.expect_toast("NVDA added to My Watchlist")
    watchlist = WatchlistPage(logged_in_page).open()
    expect(watchlist.row("NVDA")).to_be_visible()


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
def test_duplicate_watch_is_rejected(logged_in_page: Page):
    markets = MarketsPage(logged_in_page).open()
    markets.search("AAPL")
    markets.add_to_watchlist("AAPL")
    markets.expect_toast("AAPL is already in this watchlist")


@pytest.mark.ui
@pytest.mark.regression
def test_trade_link_prefills_order_ticket(logged_in_page: Page):
    markets = MarketsPage(logged_in_page).open()
    markets.search("BP")
    markets.open_trade("BP")
    expect(TradePage(logged_in_page).symbol).to_have_value("BP")
