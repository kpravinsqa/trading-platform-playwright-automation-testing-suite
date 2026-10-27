"""Central configuration. Override any value with environment variables (see README)."""
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    username: str = os.getenv("TEST_USERNAME", "demo_trader")
    password: str = os.getenv("TEST_PASSWORD", "Trade@123")
    currency_symbol: str = "£"
    min_commission: float = 5.00
    commission_rate: float = 0.001
    default_timeout_ms: int = int(os.getenv("DEFAULT_TIMEOUT_MS", "10000"))
    default_credentials: dict = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "default_credentials", {"username": self.username, "password": self.password})


settings = Settings()
