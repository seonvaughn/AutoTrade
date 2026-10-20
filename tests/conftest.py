import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scalpcity.core.config import Config, ExitRules, Sizing, WorkerConfig, validate  # noqa: E402


def make_cfg(**over) -> Config:
    workers = over.pop("workers", None) or [
        WorkerConfig(name="QQQ OG", symbol="QQQ", sizing=Sizing(mode="fixed", contracts=2),
                     daily_goal=10_000, max_daily_loss=10_000),
        WorkerConfig(name="SPY", symbol="SPY", sizing=Sizing(mode="fixed", contracts=2),
                     daily_goal=10_000, max_daily_loss=10_000),
    ]
    cfg = Config(mode="backtest", workers=workers, db_path=":memory:", **over)
    cfg.data.source = "synthetic"
    cfg.broker.name = "sim"
    cfg.dashboard.enabled = False
    cfg.risk.max_daily_loss = 100_000
    cfg.research.enabled = False  # mechanics tests; the research gate has its own tests
    cfg.research.lessons_path = ""  # tests never touch the real lessons book
    validate(cfg)
    return cfg


@pytest.fixture
def cfg():
    return make_cfg()


@pytest.fixture(autouse=True)
def _options_market():
    """Each test starts in the options market (crypto tests switch it themselves)."""
    from scalpcity.core import calendar as cal
    cal.set_market("options")
    yield
    cal.set_market("options")
