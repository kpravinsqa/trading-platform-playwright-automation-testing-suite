import re

from playwright.sync_api import Page

from pages.base_page import BasePage


def parse_money(text: str) -> float:
    return float(re.sub(r"[^0-9.\-]", "", text))


class DashboardPage(BasePage):
    path = "/dashboard.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.title = page.get_by_test_id("page-title")
        self.cash = page.get_by_test_id("cash")
        self.invested = page.get_by_test_id("invested")
        self.total_value = page.get_by_test_id("total-value")
        self.positions_table = page.get_by_test_id("positions-table")

    def cash_value(self) -> float:
        self.page.wait_for_function("document.querySelector('[data-testid=cash]').textContent.length > 0")
        return parse_money(self.cash.inner_text())

    def kpis(self) -> dict:
        self.cash_value()
        return {k: parse_money(getattr(self, k).inner_text()) for k in ("cash", "invested", "total_value")}

    def position_row(self, symbol: str):
        return self.page.get_by_test_id(f"position-{symbol}")

    def position_qty(self, symbol: str) -> int:
        return int(self.position_row(symbol).get_by_test_id("qty").inner_text())
