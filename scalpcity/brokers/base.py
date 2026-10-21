from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from ..core.events import Instrument, OrderSide


@dataclass
class Account:
    equity: float
    cash: float
    options_buying_power: float
    daytrade_count: int = 0
    pattern_day_trader: bool = False
    cash_account: bool = False


@dataclass
class OrderStatus:
    status: str          # open | partially_filled | filled | canceled | rejected | expired
    filled_qty: float
    avg_price: float

    @property
    def done(self) -> bool:
        return self.status in {"filled", "canceled", "rejected", "expired"}


class Broker(ABC):
    synchronous_fills = False  # True: submit() fills/cancels immediately (simulator)

    @abstractmethod
    async def account(self) -> Account: ...

    @abstractmethod
    async def submit(self, contract: Instrument, side: OrderSide, qty: float, limit: Optional[float]) -> str: ...

    @abstractmethod
    async def status(self, order_id: str) -> OrderStatus: ...

    @abstractmethod
    async def cancel(self, order_id: str) -> None: ...

    @abstractmethod
    async def positions(self) -> dict[str, float]:
        """Position key (OCC symbol, or coin pair without the slash) -> quantity held."""

    async def close(self) -> None:
        pass
