"""Declarative configuration for a grid backtest.

A single :class:`BotConfig` captures everything needed to build a grid strategy
and a simulated exchange and run a backtest — so a run can be described in a JSON
file and shared, versioned, or tweaked without touching code.

Part of Grid Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from grid_trading_bot.exchange import SimulatedExchange
from grid_trading_bot.grid import GridSpacing, GridStrategy


class BotConfig(BaseModel):
    """Validated configuration for a grid backtest.

    Args:
        symbol: Market symbol in ``BASE/QUOTE`` form (e.g. ``BTC/USDT``).
        lower: Bottom of the price grid.
        upper: Top of the price grid (must exceed ``lower``).
        levels: Number of grid lines (``>= 2``).
        quantity: Base quantity traded per crossed level.
        spacing: Arithmetic or geometric level distribution.
        take_profit: Optional take-profit liquidation level.
        stop_loss: Optional stop-loss liquidation level.
        trailing: Whether the grid trails an uptrend.
        cash: Starting quote balance.
        fee_rate: Proportional per-fill fee (e.g. ``0.001`` = 10 bps).
    """

    model_config = ConfigDict(frozen=True)

    symbol: str = "BTC/USDT"
    lower: float = Field(default=85.0, gt=0)
    upper: float = Field(default=115.0, gt=0)
    levels: int = Field(default=13, ge=2)
    quantity: float = Field(default=1.0, gt=0)
    spacing: GridSpacing = GridSpacing.ARITHMETIC
    take_profit: float | None = Field(default=None, gt=0)
    stop_loss: float | None = Field(default=None, gt=0)
    trailing: bool = False
    cash: float = Field(default=10_000.0, ge=0)
    fee_rate: float = Field(default=0.001, ge=0)

    @model_validator(mode="after")
    def _check_bounds(self) -> BotConfig:
        if self.upper <= self.lower:
            raise ValueError("upper must be greater than lower")
        if self.trailing and self.take_profit is not None:
            raise ValueError("trailing and take_profit cannot be combined")
        return self

    @property
    def quote(self) -> str:
        """The quote asset parsed from ``symbol``."""
        return self.symbol.split("/")[1]

    @classmethod
    def from_file(cls, path: str | Path) -> BotConfig:
        """Load and validate a :class:`BotConfig` from a JSON file."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(data)

    def to_file(self, path: str | Path) -> None:
        """Write this config to ``path`` as pretty-printed JSON."""
        Path(path).write_text(self.model_dump_json(indent=2), encoding="utf-8")

    def build_strategy(self) -> GridStrategy:
        """Construct the :class:`GridStrategy` described by this config."""
        return GridStrategy(
            lower=self.lower,
            upper=self.upper,
            levels=self.levels,
            quantity=self.quantity,
            spacing=self.spacing,
            take_profit=self.take_profit,
            stop_loss=self.stop_loss,
            trailing=self.trailing,
        )

    def build_exchange(self) -> SimulatedExchange:
        """Construct the :class:`SimulatedExchange` described by this config."""
        return SimulatedExchange(balances={self.quote: self.cash}, fee_rate=self.fee_rate)
