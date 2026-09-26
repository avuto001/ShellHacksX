"""Starter tests for services/risk.py. Run them with: pytest

Tests marked with @pytest.mark.skip are waiting for the real math to be built.
When you finish a function, delete the skip line above its test and run pytest.
"""

import pytest

from services import risk

# --- These pass today: empty or tiny inputs must return safe values ---


def test_empty_inputs_are_safe():
    assert risk.concentration({}) == 0.0
    assert risk.volatility([]) == 0.0
    assert risk.beta([], []) == 0.0
    assert risk.correlation({}) == {}
    assert risk.max_drawdown([]) == 0.0


# --- Remove the skip line once each function is built ---


@pytest.mark.skip(reason="TODO: remove this line once concentration() is built")
def test_concentration():
    assert risk.concentration({"AAPL": 5000, "MSFT": 3000}) == pytest.approx(0.625)
    assert risk.concentration({"AAPL": 1000}) == pytest.approx(1.0)


@pytest.mark.skip(reason="TODO: remove this line once volatility() is built")
def test_volatility():
    assert risk.volatility([0.01, 0.01, 0.01]) == pytest.approx(0.0)
    assert risk.volatility([0.01, -0.01, 0.01, -0.01]) > 0


@pytest.mark.skip(reason="TODO: remove this line once beta() is built")
def test_beta():
    market = [0.01, -0.02, 0.03, -0.01]
    assert risk.beta(market, market) == pytest.approx(1.0)
    double = [r * 2 for r in market]
    assert risk.beta(double, market) == pytest.approx(2.0)


@pytest.mark.skip(reason="TODO: remove this line once correlation() is built")
def test_correlation():
    result = risk.correlation({"A": [0.01, -0.02, 0.03], "B": [0.02, -0.04, 0.06]})
    assert result["A"]["B"] == pytest.approx(1.0)
    assert result["A"]["A"] == pytest.approx(1.0)


@pytest.mark.skip(reason="TODO: remove this line once max_drawdown() is built")
def test_max_drawdown():
    assert risk.max_drawdown([100, 120, 90, 110]) == pytest.approx(-0.25)
    assert risk.max_drawdown([100, 110, 120]) == pytest.approx(0.0)
