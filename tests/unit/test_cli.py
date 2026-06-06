"""Tests for the Typer CLI subcommands."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from grid_trading_bot import __version__
from grid_trading_bot.cli import app, load_prices

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_demo_runs_and_reports() -> None:
    result = runner.invoke(app, ["demo", "--levels", "9"])
    assert result.exit_code == 0
    assert "Final equity" in result.stdout


def test_demo_geometric_spacing() -> None:
    result = runner.invoke(app, ["demo", "--spacing", "geometric"])
    assert result.exit_code == 0


def test_demo_rejects_bad_grid() -> None:
    result = runner.invoke(app, ["demo", "--lower", "200", "--upper", "100"])
    assert result.exit_code == 1


def test_init_config_and_backtest(tmp_path: Path) -> None:
    cfg_path = tmp_path / "grid.json"
    res1 = runner.invoke(app, ["init-config", str(cfg_path)])
    assert res1.exit_code == 0
    assert cfg_path.exists()

    res2 = runner.invoke(app, ["backtest", str(cfg_path)])
    assert res2.exit_code == 0
    assert "Backtest" in res2.stdout


def test_init_config_refuses_overwrite(tmp_path: Path) -> None:
    cfg_path = tmp_path / "grid.json"
    runner.invoke(app, ["init-config", str(cfg_path)])
    result = runner.invoke(app, ["init-config", str(cfg_path)])
    assert result.exit_code == 1


def test_backtest_with_prices_file(tmp_path: Path) -> None:
    cfg_path = tmp_path / "grid.json"
    runner.invoke(app, ["init-config", str(cfg_path)])
    prices = tmp_path / "p.csv"
    prices.write_text("\n".join(str(90 + i % 30) for i in range(60)), encoding="utf-8")
    result = runner.invoke(app, ["backtest", str(cfg_path), "--prices", str(prices)])
    assert result.exit_code == 0


def test_load_prices_parses_csv(tmp_path: Path) -> None:
    p = tmp_path / "p.csv"
    p.write_text("100\n101.5,extra\n\n102\n", encoding="utf-8")
    assert load_prices(p) == [100.0, 101.5, 102.0]
