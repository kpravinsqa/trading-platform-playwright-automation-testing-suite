from playwright.sync_api import Page

from pages.base_page import BasePage


class OrdersPage(BasePage):
    path = "/orders.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.status_filter = page.get_by_test_id("status-filter")
        self.rows = page.get_by_test_id("orders-table").locator("tbody tr")
        self.empty_state = page.get_by_test_id("no-orders")

    def row(self, order_id: int):
        return self.page.get_by_test_id(f"order-{order_id}")

    def status_of(self, order_id: int):
        return self.row(order_id).get_by_test_id("status")

    def cancel(self, order_id: int):
        self.page.get_by_test_id(f"cancel-{order_id}").click()

    def filter_by(self, status: str):
        self.status_filter.select_option(status)
