"""Authentication — maps to manual suite TS-01 (Login & Session)."""
import re

import pytest
from playwright.sync_api import Page, expect

from config.settings import settings
from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from utils.data_loader import cases

LOGIN_URL = re.compile(r".*/login\.html$")


@pytest.mark.ui
@pytest.mark.smoke
def test_valid_login_lands_on_portfolio(page: Page):
    login = LoginPage(page).open()
    login.login(settings.username, settings.password)
    login.wait_for_post_login()
    dashboard = DashboardPage(page)
    expect(dashboard.title).to_have_text("Portfolio")
    expect(dashboard.user_badge).to_have_text("Demo Trader")


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.parametrize("case", cases("login", "invalid_credentials"))
def test_invalid_credentials_are_rejected(page: Page, case):
    login = LoginPage(page).open()
    login.login(case["username"], case["password"])
    login.expect_form_error(case["error"])
    expect(page).to_have_url(LOGIN_URL)


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.parametrize("case", cases("login", "empty_fields"))
def test_mandatory_field_validation(page: Page, case):
    login = LoginPage(page).open()
    login.login(case["username"], case["password"])
    for field, message in case["errors"].items():
        expect(login.field_error(field)).to_have_text(message)


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
def test_locked_account_cannot_sign_in(page: Page):
    login = LoginPage(page).open()
    login.login("locked_user", "Trade@123")
    login.expect_form_error("Account locked. Please contact support.")


@pytest.mark.ui
@pytest.mark.regression
def test_account_locks_after_three_failed_attempts(page: Page):
    login = LoginPage(page).open()
    for _ in range(2):
        login.login(settings.username, "bad-password")
        login.expect_form_error("Invalid username or password")
    login.login(settings.username, "bad-password")
    login.expect_form_error("Account locked. Please contact support.")
    # even the correct password is now refused
    login.login(settings.username, settings.password)
    login.expect_form_error("Account locked. Please contact support.")


@pytest.mark.ui
@pytest.mark.smoke
def test_logout_clears_session_and_protects_pages(logged_in_page: Page):
    DashboardPage(logged_in_page).logout()
    logged_in_page.goto("/dashboard.html")
    expect(logged_in_page).to_have_url(LOGIN_URL)


@pytest.mark.ui
@pytest.mark.regression
def test_password_field_is_masked(page: Page):
    expect(LoginPage(page).open().password).to_have_attribute("type", "password")
