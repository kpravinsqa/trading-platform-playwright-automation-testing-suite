from playwright.sync_api import Page

from pages.base_page import BasePage


class TradePage(BasePage):
    path = "/trade.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.symbol = page.get_by_test_id("symbol")
        self.side = page.get_by_test_id("side")
        self.order_type = page.get_by_test_id("order-type")
        self.quantity = page.get_by_test_id("quantity")
        self.limit_price = page.get_by_test_id("limit-price")
        self.preview_button = page.get_by_test_id("preview-order")
        self.place_button = page.get_by_test_id("place-order")
        self.preview_panel = page.get_by_test_id("preview-panel")
        self.preview_commission = page.get_by_test_id("preview-commission")
        self.preview_notional = page.get_by_test_id("preview-notional")
        self.preview_total = page.get_by_test_id("preview-total")
        self.confirmation = page.get_by_test_id("confirmation")
        self.confirm_status = page.get_by_test_id("confirm-status")
        self.confirm_id = page.get_by_test_id("confirm-id")

    def open_for(self, symbol: str):
        self.page.goto(f"{self.path}?symbol={symbol}")
        return self

    def fill_order(self, symbol=None, side="BUY", order_type="MARKET", quantity=None, limit_price=None):
        if symbol is not None:
            self.symbol.fill(symbol)
        self.side.select_option(side)
        self.order_type.select_option(order_type)
        if quantity is not None:
            self.quantity.fill(str(quantity))
        if limit_price is not None:
            self.limit_price.fill(str(limit_price))

    def preview(self):
        self.preview_button.click()

    def place(self):
        self.place_button.click()
