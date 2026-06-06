"""Tests for the BotConfig loader/validator and builders."""

from __future__ import annotations

from pathlib import Path

import pytest

from grid_trading_bot.config import BotConfig
from grid_trading_bot.grid import GridSpacing, GridStrategy


def test_defaults_are_valid() -> None:
    cfg = BotConfig()
    assert cfg.symbol == "BTC/USDT"
    assert cfg.quote == "USDT"
    assert isinstance(cfg.build_strategy(), GridStrategy)


def test_round_trip_to_and_from_file(tmp_path: Path) -> None:
    cfg = BotConfig(lower=10.0, upper=20.0, spacing=GridSpacing.GEOMETRIC, take_profit=25.0)
    path = tmp_path / "grid.json"
    cfg.to_file(path)
    loaded = BotConfig.from_file(path)
    assert loaded == cfg
    assert loaded.spacing is GridSpacing.GEOMETRIC


def test_upper_must_exceed_lower() -> None:
    with pytest.raises(ValueError):
        BotConfig(lower=100.0, upper=50.0)


def test_trailing_with_take_profit_rejected() -> None:
    with pytest.raises(ValueError):
        BotConfig(trailing=True, take_profit=200.0)


def test_build_exchange_funds_quote_asset() -> None:
    cfg = BotConfig(symbol="ETH/USDC", cash=5_000.0)
    ex = cfg.build_exchange()
    assert ex.balance("USDC") == 5_000.0
    assert cfg.quote == "USDC"


def test_negative_fee_rejected() -> None:
    with pytest.raises(ValueError):
        BotConfig(fee_rate=-0.1)
