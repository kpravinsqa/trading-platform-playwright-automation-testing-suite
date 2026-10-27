"""Watchlist management — maps to manual suite TS-03 (Watchlists)."""
import pytest
from playwright.sync_api import Page, expect

from pages.watchlist_page import WatchlistPage


@pytest.fixture
def watchlist(logged_in_page: Page) -> WatchlistPage:
    return WatchlistPage(logged_in_page).open()


@pytest.mark.ui
@pytest.mark.smoke
def test_create_watchlist(watchlist: WatchlistPage):
    watchlist.create("Tech Growth")
    watchlist.expect_toast('Watchlist "Tech Growth" created')
    expect(watchlist.selector).to_contain_text("Tech Growth")
    expect(watchlist.empty_state).to_be_visible()


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.parametrize("name, error", [
    ("", "Watchlist name is required"),
    ("My Watchlist", "A watchlist with this name already exists"),
    ("my watchlist", "A watchlist with this name already exists"),
    ("X" * 31, "Name must be 30 characters or fewer"),
], ids=["empty", "duplicate", "duplicate-case-insensitive", "31-chars"])
def test_watchlist_name_validation(watchlist: WatchlistPage, name, error):
    watchlist.create(name)
    expect(watchlist.name_error).to_have_text(error)


@pytest.mark.ui
@pytest.mark.regression
def test_watchlist_name_at_max_length_is_accepted(watchlist: WatchlistPage):
    name = "W" * 30
    watchlist.create(name)
    watchlist.expect_toast(f'Watchlist "{name}" created')


@pytest.mark.ui
@pytest.mark.regression
def test_add_and_view_symbols(watchlist: WatchlistPage):
    watchlist.add_symbol("TSLA")
    watchlist.expect_toast("Instrument added")
    expect(watchlist.rows).to_have_count(3)
    assert watchlist.symbols() == ["AAPL", "MSFT", "TSLA"]


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.defect
def test_remove_selected_removes_only_checked_rows(watchlist: WatchlistPage):
    """Regression guard: removing a selection once deleted unselected instruments too."""
    for s in ("TSLA", "NVDA", "BP"):
        watchlist.add_symbol(s)
        expect(watchlist.row(s)).to_be_visible()
    watchlist.select("MSFT", "NVDA")
    expect(watchlist.selected_count).to_have_text("2 selected")
    watchlist.remove_selected.click()
    watchlist.expect_toast("2 instrument(s) removed")
    expect(watchlist.rows).to_have_count(3)
    assert watchlist.symbols() == ["AAPL", "TSLA", "BP"]


@pytest.mark.ui
@pytest.mark.regression
def test_select_all_then_remove_empties_watchlist(watchlist: WatchlistPage):
    watchlist.select_all.check()
    expect(watchlist.selected_count).to_have_text("2 selected")
    watchlist.remove_selected.click()
    expect(watchlist.empty_state).to_be_visible()


@pytest.mark.ui
@pytest.mark.regression
def test_remove_button_disabled_until_selection(watchlist: WatchlistPage):
    expect(watchlist.remove_selected).to_be_disabled()
    watchlist.select("AAPL")
    expect(watchlist.remove_selected).to_be_enabled()


@pytest.mark.ui
@pytest.mark.regression
def test_delete_custom_watchlist(watchlist: WatchlistPage):
    watchlist.create("Short Term")
    watchlist.expect_toast('Watchlist "Short Term" created')
    watchlist.delete_button.click()
    watchlist.expect_toast('Watchlist "Short Term" deleted')
    expect(watchlist.selector).not_to_contain_text("Short Term")


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
def test_default_watchlist_cannot_be_deleted(watchlist: WatchlistPage):
    expect(watchlist.delete_button).to_be_disabled()
