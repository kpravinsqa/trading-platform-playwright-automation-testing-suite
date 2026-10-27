# Trading Platform — Python + Playwright Test Automation

![Tests](https://github.com/kpravinsqa/playwright-python-trading-platform/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Playwright](https://img.shields.io/badge/playwright-python-2EAD33) ![Pytest](https://img.shields.io/badge/pytest-8.x-0A9EDC)

End-to-end UI and API automation framework for an **online share-dealing / investment platform**, modelled on the
business flows I tested on the **CMC Invest (Investment Banking / Equities)** project: login and account lockout,
instrument search, watchlists, the order ticket (market and limit orders, commission), positions and order history.

> **Confidentiality note:** this is an original portfolio project. It contains **no proprietary code, data, URLs or
> screens** from any employer or client. The system under test is a small mock application in `mock_app/`
> that I wrote to reproduce the domain rules, so the suite runs anywhere, including GitHub Actions.

## Highlights

| Area | What it demonstrates |
|---|---|
| **Page Object Model** | One class per screen in `pages/`, locators by `data-testid`, no raw selectors in tests |
| **UI + API layers** | Browser tests (`tests/ui`) and pure API tests (`tests/api`) through Playwright's `APIRequestContext` |
| **Data-driven** | Boundary values, commission rules and negative logins in `test_data/*.json` with readable test IDs |
| **Contract testing** | `jsonschema` validation of order, account and instrument payloads |
| **Defect regression guards** | `@pytest.mark.defect` tests reproduce real production bug patterns (e.g. watchlist multi-select deletion) |
| **Isolation** | Server state is reset before every test, so tests run in parallel (`pytest-xdist`) without interfering |
| **CI/CD** | GitHub Actions matrix (smoke / regression), nightly schedule, HTML report and failure screenshots as artifacts |

## Project structure

```
├── api/                 # API service client + JSON schemas
├── config/settings.py   # env-driven configuration (credentials, timeouts)
├── mock_app/            # system under test: stdlib HTTP server + static front end
├── pages/               # Page Objects (login, dashboard, markets, watchlists, trade, orders)
├── test_data/           # JSON data sets for parametrised tests
├── tests/
│   ├── ui/              # Playwright browser tests
│   └── api/             # REST API tests
├── utils/               # logger, data loader
├── conftest.py          # server lifecycle, base_url, auth fixtures, state reset
└── .github/workflows/   # CI pipeline
```

## Coverage (82 automated checks)

| Suite | Module | Key scenarios |
|---|---|---|
| TS-01 | Login & session | valid login, invalid credentials (incl. SQL-injection string), mandatory fields, locked account, lockout after 3 failures, logout and protected routes |
| TS-02 | Markets | search by symbol/name, case-insensitivity, empty state, suspended instruments, add to watchlist, trade deep link |
| TS-03 | Watchlists | create, name validation (empty / duplicate / 30 vs 31 chars), add symbols, **remove only selected rows**, select-all, delete, default list protected, max-10 rule |
| TS-04 | Order ticket | market buy, commission preview (min £5 vs 0.1%), quantity boundaries 0/1/2/9 999/10 000/10 001, insufficient funds, insufficient holdings, suspended instrument, limit price rules |
| TS-05 | Orders & positions | pending limit order → cancel, status filter, average-price recalculation, cash movement, per-user data isolation |

## Getting started

```bash
git clone https://github.com/kpravinsqa/playwright-python-trading-platform.git
cd playwright-python-trading-platform
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium

pytest                       # full suite, HTML report in reports/report.html
pytest -m smoke              # critical path only
pytest -m api                # API layer only
pytest -n auto               # parallel
pytest --headed --slowmo 300 # watch the browser
```

Explore the app manually: `python -m mock_app.server` then open http://127.0.0.1:8000 (user `demo_trader` / `Trade@123`).

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `BASE_URL` | *(bundled mock app)* | Point the suite at another deployed environment |
| `TEST_USERNAME` / `TEST_PASSWORD` | `demo_trader` / `Trade@123` | Credentials for the default user |

## Business rules under test

* Commission = **max(£5.00, 0.10 % of notional)**, rounded to 2 dp
* Quantity: whole number **1 – 10,000**
* Limit BUY fills immediately when limit ≥ market price, otherwise rests as `PENDING`
* 3 consecutive failed logins lock the account
* Watchlists: max 10, names unique (case-insensitive), ≤ 30 characters; the default list cannot be deleted

## Author

**Pravin Khedkar**, QA Lead / SDET (Python · Playwright · API · SQL · AI/LLM testing)
GitHub [@kpravinsqa](https://github.com/kpravinsqa)
