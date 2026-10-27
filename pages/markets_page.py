from playwright.sync_api import Page

from pages.base_page import BasePage


class MarketsPage(BasePage):
    path = "/markets.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.search_input = page.get_by_test_id("search-input")
        self.search_button = page.get_by_test_id("search-button")
        self.result_count = page.get_by_test_id("result-count")
        self.rows = page.get_by_test_id("instrument-table").locator("tbody tr")
        self.no_results = page.get_by_test_id("no-results")

    def search(self, term: str):
        self.search_input.fill(term)
        with self.page.expect_response("**/api/instruments?q=*"):
            self.search_button.click()
        self.page.wait_for_load_state("networkidle")

    def row(self, symbol: str):
        return self.page.get_by_test_id(f"row-{symbol}")

    def add_to_watchlist(self, symbol: str):
        self.page.get_by_test_id(f"watch-{symbol}").click()

    def open_trade(self, symbol: str):
        self.page.get_by_test_id(f"trade-{symbol}").click()
