"""Tests for services/risk.py. Run them with: pytest

Every test uses a small made-up price table where we know the right answer,
so no internet is needed.
"""

import pandas as pd
import pytest

from services import risk


def make_prices(columns):
    """Build a price table from {"AAPL": [100, 101, ...], ...}, one row per day."""
    days = pd.date_range("2026-01-01", periods=len(next(iter(columns.values()))), freq="D")
    return pd.DataFrame(columns, index=days)


# --- daily_returns ---


def test_daily_returns_are_percent_changes():
    prices = make_prices({"AAPL": [100, 110, 99]})
    returns = risk.daily_returns(prices)
    # 100 -> 110 is +10%, 110 -> 99 is -10%; the first day has no return
    assert list(returns["AAPL"]) == pytest.approx([0.10, -0.10])


# --- portfolio_weights and sector_weights ---


def test_equal_holdings_give_equal_weights():
    weights = risk.portfolio_weights({"AAPL": 10, "MSFT": 10}, {"AAPL": 50.0, "MSFT": 50.0})
    assert weights["AAPL"] == pytest.approx(0.5)
    assert weights["MSFT"] == pytest.approx(0.5)


def test_weights_use_value_not_share_count():
    # 10 x $300 = $3,000 and 10 x $100 = $1,000, so 75% / 25%
    weights = risk.portfolio_weights({"AAPL": 10, "F": 10}, {"AAPL": 300.0, "F": 100.0})
    assert weights["AAPL"] == pytest.approx(0.75)
    assert weights["F"] == pytest.approx(0.25)
    assert sum(weights.values()) == pytest.approx(1.0)


def test_weights_skip_stocks_without_a_price():
    weights = risk.portfolio_weights({"AAPL": 10, "XYZ": 10}, {"AAPL": 50.0})
    assert weights == {"AAPL": pytest.approx(1.0)}


def test_empty_portfolio_has_no_weights():
    assert risk.portfolio_weights({}, {}) == {}


def test_sector_weights_add_up_by_industry():
    weights = {"AAPL": 0.5, "MSFT": 0.3, "JNJ": 0.2}
    sectors = {"AAPL": "Technology", "MSFT": "Technology", "JNJ": "Healthcare"}
    result = risk.sector_weights(weights, sectors)
    assert result["Technology"] == pytest.approx(0.8)
    assert result["Healthcare"] == pytest.approx(0.2)


def test_unknown_sector():
    assert risk.sector_weights({"XYZ": 1.0}, {}) == {"Unknown": 1.0}


# --- portfolio_volatility ---


def test_steady_growth_has_zero_volatility():
    # Grows exactly 1% every day: no swings at all
    returns = risk.daily_returns(make_prices({"A": [100, 101, 102.01, 103.0301]}))
    assert risk.portfolio_volatility(returns, {"A": 1.0}) == pytest.approx(0.0)


def test_volatility_is_yearly_standard_deviation():
    returns = risk.daily_returns(make_prices({"A": [100, 110, 99, 108.9]}))
    expected = returns["A"].std() * (252 ** 0.5)
    assert risk.portfolio_volatility(returns, {"A": 1.0}) == pytest.approx(expected)


def test_volatility_needs_two_days():
    returns = risk.daily_returns(make_prices({"A": [100, 110]}))
    assert risk.portfolio_volatility(returns, {"A": 1.0}) is None


# --- portfolio_beta ---


def test_stock_identical_to_spy_has_beta_of_one():
    prices = make_prices({"A": [100, 102, 99, 104, 103], "SPY": [100, 102, 99, 104, 103]})
    returns = risk.daily_returns(prices)
    assert risk.portfolio_beta(returns, {"A": 1.0}, returns["SPY"]) == pytest.approx(1.0)


def test_stock_moving_twice_as_much_has_beta_of_two():
    spy = [0.01, -0.02, 0.03, -0.01]
    returns = pd.DataFrame({"A": [r * 2 for r in spy], "SPY": spy})
    assert risk.portfolio_beta(returns, {"A": 1.0}, returns["SPY"]) == pytest.approx(2.0)


def test_flat_market_gives_no_beta():
    returns = pd.DataFrame({"A": [0.01, -0.02, 0.03], "SPY": [0.0, 0.0, 0.0]})
    assert risk.portfolio_beta(returns, {"A": 1.0}, returns["SPY"]) is None


# --- correlation_matrix ---


def test_stocks_moving_in_step_have_correlation_one():
    returns = pd.DataFrame({"A": [0.01, -0.02, 0.03], "B": [0.02, -0.04, 0.06], "SPY": [0.01, 0.0, 0.01]})
    matrix = risk.correlation_matrix(returns)
    assert matrix.loc["A", "B"] == pytest.approx(1.0)
    # SPY is left out
    assert "SPY" not in matrix.columns


def test_opposite_stocks_have_correlation_minus_one():
    returns = pd.DataFrame({"A": [0.01, -0.02, 0.03], "B": [-0.01, 0.02, -0.03]})
    assert risk.correlation_matrix(returns).loc["A", "B"] == pytest.approx(-1.0)


def test_one_stock_has_no_correlation_matrix():
    returns = pd.DataFrame({"A": [0.01, -0.02], "SPY": [0.01, 0.0]})
    assert risk.correlation_matrix(returns) is None


# --- max_drawdown ---


def test_drawdown_100_to_80_to_90_is_minus_20_percent():
    returns = risk.daily_returns(make_prices({"A": [100, 80, 90]}))
    assert risk.max_drawdown(returns, {"A": 1.0}) == pytest.approx(-0.20)


def test_drawdown_measures_from_the_highest_point():
    # Peak 120 -> low 90 is a 25% drop
    returns = risk.daily_returns(make_prices({"A": [100, 120, 90, 110]}))
    assert risk.max_drawdown(returns, {"A": 1.0}) == pytest.approx(-0.25)


def test_only_going_up_has_no_drawdown():
    returns = risk.daily_returns(make_prices({"A": [100, 110, 120]}))
    assert risk.max_drawdown(returns, {"A": 1.0}) == pytest.approx(0.0)


# --- risk_warnings ---


def test_no_warnings_for_a_spread_out_portfolio():
    weights = {"A": 0.25, "B": 0.25, "C": 0.25, "D": 0.25}
    sectors = {"Tech": 0.5, "Health": 0.5}
    correlation = pd.DataFrame([[1, 0.2], [0.2, 1]], index=["A", "B"], columns=["A", "B"])
    assert risk.risk_warnings(weights, sectors, correlation) == []


def test_warning_for_one_big_stock():
    warnings = risk.risk_warnings({"AAPL": 0.7, "MSFT": 0.3}, {"Tech": 0.5, "Other": 0.5}, None)
    assert len(warnings) == 1
    assert "AAPL is 70%" in warnings[0]


def test_warning_for_one_big_sector():
    warnings = risk.risk_warnings({"A": 0.35, "B": 0.35, "C": 0.3}, {"Technology": 0.7, "Health": 0.3}, None)
    assert len(warnings) == 1
    assert "Technology" in warnings[0]


def test_warning_for_stocks_that_move_together():
    correlation = pd.DataFrame([[1, 0.9], [0.9, 1]], index=["A", "B"], columns=["A", "B"])
    warnings = risk.risk_warnings({"A": 0.4, "B": 0.4, "C": 0.2}, {"X": 0.5, "Y": 0.5}, correlation)
    assert len(warnings) == 1
    assert "move together" in warnings[0]


# --- analyze_portfolio (with fake price data instead of the internet) ---


def use_fake_prices(monkeypatch, prices):
    risk.analyze_portfolio.clear()  # forget cached results from other tests
    monkeypatch.setattr(risk, "get_history_for_many", lambda tickers, period: prices)


def test_analyze_portfolio_fills_everything_in(monkeypatch):
    prices = make_prices({
        "AAPL": [100, 102, 99, 104, 103],
        "MSFT": [200, 203, 199, 206, 205],
        "SPY": [400, 404, 398, 408, 406],
    })
    use_fake_prices(monkeypatch, prices)
    result = risk.analyze_portfolio({"AAPL": 2, "MSFT": 1}, {"AAPL": "Technology", "MSFT": "Technology"})
    # 2 x $103 = $206 and 1 x $205 = $205
    assert result["weights"]["AAPL"] == pytest.approx(206 / 411)
    assert result["sector_weights"]["Technology"] == pytest.approx(1.0)
    assert result["volatility"] > 0
    assert result["beta"] is not None
    assert result["correlation"] is not None
    assert result["max_drawdown"] < 0
    # Both stocks are 100% Technology, and they move together
    assert len(result["warnings"]) >= 2
    assert result["missing"] == []


def test_analyze_portfolio_with_one_stock(monkeypatch):
    use_fake_prices(monkeypatch, make_prices({"AAPL": [100, 80, 90], "SPY": [400, 390, 395]}))
    result = risk.analyze_portfolio({"AAPL": 5}, {"AAPL": "Technology"})
    assert result["weights"] == {"AAPL": pytest.approx(1.0)}
    assert result["correlation"] is None  # can't correlate one stock
    assert result["max_drawdown"] == pytest.approx(-0.20)


def test_analyze_portfolio_with_no_price_data(monkeypatch):
    use_fake_prices(monkeypatch, pd.DataFrame())
    result = risk.analyze_portfolio({"AAPL": 5}, {"AAPL": "Technology"})
    assert result["weights"] == {}
    assert result["volatility"] is None
    assert result["missing"] == ["AAPL"]


def test_analyze_portfolio_without_spy(monkeypatch):
    use_fake_prices(monkeypatch, make_prices({"AAPL": [100, 102, 99, 104]}))
    result = risk.analyze_portfolio({"AAPL": 5}, {})
    assert result["beta"] is None  # no market data to compare with
    assert result["volatility"] is not None


def test_analyze_empty_portfolio(monkeypatch):
    use_fake_prices(monkeypatch, pd.DataFrame())
    result = risk.analyze_portfolio({}, {})
    assert result["weights"] == {}
    assert result["warnings"] == []
