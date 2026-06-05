"""Core value objects shared across the grid trading bot.

Defines the ``Side`` enum, an immutable ``Order``, and an immutable ``Fill``
returned by the exchange once an order is executed.

Part of Grid Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Side(str, Enum):
    """Direction of an order."""

    BUY = "buy"
    SELL = "sell"


class Order(BaseModel):
    """An instruction to trade ``quantity`` of ``symbol`` at ``price``.

    Args:
        symbol: Market symbol in ``BASE/QUOTE`` form (e.g. ``BTC/USDT``).
        side: Whether to buy or sell.
        quantity: Base-asset quantity to trade (must be positive).
        price: Limit/fill price in the quote asset (must be positive).
    """

    model_config = ConfigDict(frozen=True)

    symbol: str
    side: Side
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)

    @property
    def notional(self) -> float:
        """Quote-asset value of the order, ``price * quantity``."""
        return self.price * self.quantity


class Fill(BaseModel):
    """The result of executing an :class:`Order`, including the fee paid.

    Args:
        order: The order that was executed.
        fee: Fee charged in the quote asset (non-negative).
    """

    model_config = ConfigDict(frozen=True)

    order: Order
    fee: float = Field(ge=0)
