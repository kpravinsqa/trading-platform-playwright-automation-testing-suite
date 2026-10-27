from playwright.sync_api import Page

from pages.base_page import BasePage


class WatchlistPage(BasePage):
    path = "/watchlists.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.name_input = page.get_by_test_id("watchlist-name")
        self.create_button = page.get_by_test_id("create-watchlist")
        self.name_error = page.get_by_test_id("error-name")
        self.selector = page.get_by_test_id("watchlist-select")
        self.delete_button = page.get_by_test_id("delete-watchlist")
        self.symbol_input = page.get_by_test_id("add-symbol-input")
        self.add_button = page.get_by_test_id("add-symbol")
        self.rows = page.get_by_test_id("watchlist-table").locator("tbody tr")
        self.select_all = page.get_by_test_id("select-all")
        self.remove_selected = page.get_by_test_id("remove-selected")
        self.selected_count = page.get_by_test_id("selected-count")
        self.empty_state = page.get_by_test_id("empty-watchlist")

    def open(self):
        super().open()
        self.selector.locator("option").first.wait_for(state="attached")
        return self

    def create(self, name: str):
        self.name_input.fill(name)
        self.create_button.click()

    def choose(self, name: str):
        self.selector.select_option(label=name)

    def add_symbol(self, symbol: str):
        self.symbol_input.fill(symbol)
        self.add_button.click()

    def select(self, *symbols: str):
        for s in symbols:
            self.page.get_by_test_id(f"select-{s}").check()

    def symbols(self) -> list[str]:
        return [t.removeprefix("wl-row-") for t in self.rows.evaluate_all("rows => rows.map(r => r.dataset.testid)")]

    def row(self, symbol: str):
        return self.page.get_by_test_id(f"wl-row-{symbol}")
