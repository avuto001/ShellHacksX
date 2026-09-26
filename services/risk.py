"""Portfolio math: concentration, volatility, beta, correlation and drawdown.

These functions only do math. They don't call any APIs, which makes them easy to
test (see tests/test_risk.py). The page that shows the results is
pages/3_Portfolio_Risk.py.

Tip: numpy and pandas are already installed (Streamlit depends on them).

"Returns" below means daily percent changes as decimals, e.g. a stock that went
from $100 to $102 has a return of 0.02.
"""


def concentration(values):
    """How much of the portfolio sits in its single biggest holding.

    Input:
        values: dollar value of each holding, e.g. {"AAPL": 5000, "MSFT": 3000}
    Output:
        The biggest holding's share of the total, from 0.0 to 1.0
        (e.g. 5000 / 8000 = 0.625). Returns 0.0 for an empty portfolio.
    """
    # TODO: build this
    return 0.0


def volatility(returns):
    """How much a stock's price swings, as a yearly number.

    Input:
        returns: list of daily returns, e.g. [0.01, -0.02, 0.005]
    Output:
        Annualized volatility: the standard deviation of the daily returns times
        the square root of 252 (trading days per year). Returns 0.0 if there are
        fewer than 2 returns.
    """
    # TODO: build this
    return 0.0


def beta(stock_returns, market_returns):
    """How much a stock moves compared to the whole market.

    Inputs:
        stock_returns:  list of the stock's daily returns
        market_returns: list of the market's daily returns (e.g. SPY) for the same days
    Output:
        covariance(stock, market) / variance(market).
        1.0 = moves with the market, 2.0 = moves twice as much, 0.5 = half as much.
        Returns 0.0 if the lists are empty, different lengths or the market never moved.
    """
    # TODO: build this
    return 0.0


def correlation(returns_by_ticker):
    """How closely each pair of stocks moves together.

    Input:
        returns_by_ticker: e.g. {"AAPL": [0.01, -0.02], "MSFT": [0.02, -0.01]}
    Output:
        A nested dict like {"AAPL": {"AAPL": 1.0, "MSFT": 0.8}, "MSFT": {...}}.
        1.0 = always move together, 0 = unrelated, -1.0 = always move opposite.
        Returns {} if there are fewer than 2 tickers.
    """
    # TODO: build this
    return {}


def max_drawdown(prices):
    """The biggest drop from a peak to a later low.

    Input:
        prices: list of prices in date order, e.g. [100, 120, 90, 110]
    Output:
        The largest drop as a negative decimal. For the example: peak 120 -> low 90
        is (90 - 120) / 120 = -0.25. Returns 0.0 if prices never fall or the list
        has fewer than 2 prices.
    """
    # TODO: build this
    return 0.0
