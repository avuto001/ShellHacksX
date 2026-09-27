"""Portfolio risk math for StockSense.

Inputs:
  holdings: how many shares of each stock, e.g. {"AAPL": 10, "MSFT": 5}
  sectors:  each stock's industry, e.g. {"AAPL": "Technology", "MSFT": "Technology"}

Words used below:
  prices  - a pandas table: one row per day, one column per ticker
  returns - the same shape, but each number is the day's percent change as a
            decimal (a stock going from $100 to $102 has a return of 0.02)
  weights - each stock's share of the portfolio's value, e.g. {"AAPL": 0.6, "MSFT": 0.4}

"SPY" is a fund that tracks the 500 biggest US companies, so we use it as "the market".
"""

import numpy as np
import pandas as pd
import streamlit as st

from services.price_history import get_history_for_many

MARKET = "SPY"
TRADING_DAYS_PER_YEAR = 252

# Warning thresholds
MAX_STOCK_WEIGHT = 0.40
MAX_SECTOR_WEIGHT = 0.60
MAX_AVERAGE_CORRELATION = 0.70


def daily_returns(prices):
    """Turn a table of daily prices into a table of daily percent changes."""
    # pct_change() works out (today - yesterday) / yesterday for every column
    returns = prices.pct_change()

    # The first day has no "yesterday", and stocks may be missing some days.
    # Keep only the days where every column has a number, so they all line up.
    returns = returns.dropna()
    return returns


def portfolio_weights(holdings, latest_prices):
    """Work out each stock's share of the total value. The weights add up to 1."""
    # Value of each holding = shares x latest price
    values = {}
    for ticker in holdings:
        if ticker in latest_prices:
            values[ticker] = holdings[ticker] * latest_prices[ticker]

    # Add up the total value
    total = 0.0
    for ticker in values:
        total = total + values[ticker]

    # Nothing to divide by: return no weights
    if total <= 0:
        return {}

    # Each weight = this stock's value / total value
    weights = {}
    for ticker in values:
        weights[ticker] = values[ticker] / total
    return weights


def sector_weights(weights, sectors):
    """Add up the weights of stocks in the same industry."""
    totals = {}
    for ticker in weights:
        # Stocks with no known industry go under "Unknown"
        sector = sectors.get(ticker) or "Unknown"
        if sector not in totals:
            totals[sector] = 0.0
        totals[sector] = totals[sector] + weights[ticker]
    return totals


def _portfolio_returns(returns, weights):
    """The whole portfolio's return each day: each stock's return times its weight, added up."""
    total = pd.Series(0.0, index=returns.index)
    for ticker in weights:
        if ticker in returns.columns:
            total = total + returns[ticker] * weights[ticker]
    return total


def portfolio_volatility(returns, weights):
    """How much the portfolio's value swings, as a yearly number (0.20 means about 20% a year).

    Returns None if there aren't enough days of data.
    """
    daily = _portfolio_returns(returns, weights)
    if len(daily) < 2:
        return None

    # Standard deviation = how far a typical day is from the average day
    daily_std = daily.std()

    # Multiply by the square root of 252 (trading days in a year) to make it yearly
    return float(daily_std * np.sqrt(TRADING_DAYS_PER_YEAR))


def portfolio_beta(returns, weights, market_returns):
    """How much the portfolio moves when the market moves (1.0 = same as the market).

    Returns None if there isn't enough data or the market never moved.
    """
    daily = _portfolio_returns(returns, weights)

    # Only compare days that both the portfolio and the market have
    both = pd.DataFrame({"portfolio": daily, "market": market_returns}).dropna()
    if len(both) < 2:
        return None

    # Variance = how much the market swings on its own
    market_variance = both["market"].var()
    if market_variance == 0:
        return None

    # Covariance = how much the portfolio and market swing together
    covariance = both["portfolio"].cov(both["market"])
    return float(covariance / market_variance)


def correlation_matrix(returns):
    """How closely each pair of stocks moves together, from -1 (opposite) to 1 (in step).

    SPY is left out, because it's the market, not one of your stocks.
    Returns None if there are fewer than 2 stocks.
    """
    stock_columns = []
    for ticker in returns.columns:
        if ticker != MARKET:
            stock_columns.append(ticker)

    if len(stock_columns) < 2:
        return None
    return returns[stock_columns].corr()


def max_drawdown(returns, weights):
    """The biggest drop from a high point in the portfolio's value, e.g. -0.20 for a 20% drop."""
    daily = _portfolio_returns(returns, weights)

    # Pretend we start with $1 and follow it day by day
    value = 1.0
    peak = 1.0  # the highest value so far
    worst_drop = 0.0

    for day_return in daily:
        # Grow (or shrink) the value by today's return
        value = value * (1 + day_return)

        # A new high? Remember it
        if value > peak:
            peak = value

        # How far below the highest point are we now?
        drop = (value - peak) / peak
        if drop < worst_drop:
            worst_drop = drop

    return float(worst_drop)


def _average_correlation(correlation):
    """The average correlation over every pair of different stocks."""
    tickers = list(correlation.columns)
    total = 0.0
    pairs = 0

    # Visit each pair once (AAPL-MSFT, but not MSFT-AAPL again or AAPL-AAPL)
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            total = total + correlation.iloc[i, j]
            pairs = pairs + 1

    if pairs == 0:
        return None
    return total / pairs


def risk_warnings(weights, sector_weights, correlation):
    """Return a list of plain-English warnings about the portfolio (empty if none)."""
    warnings = []

    # One stock is too big a part of the portfolio
    for ticker in weights:
        if weights[ticker] > MAX_STOCK_WEIGHT:
            percent = round(weights[ticker] * 100)
            warnings.append(
                f"{ticker} is {percent}% of your portfolio. If it has a bad day, your whole portfolio feels it."
            )

    # One industry is too big a part of the portfolio
    for sector in sector_weights:
        if sector_weights[sector] > MAX_SECTOR_WEIGHT:
            percent = round(sector_weights[sector] * 100)
            warnings.append(
                f"{percent}% of your money is in {sector}. News that hurts that industry could hit most of your stocks at once."
            )

    # The stocks tend to move together
    if correlation is not None:
        average = _average_correlation(correlation)
        if average is not None and average > MAX_AVERAGE_CORRELATION:
            warnings.append(
                f"Your stocks tend to move together (average correlation {average:.2f}). "
                "When one falls, the others often fall too."
            )

    return warnings


@st.cache_data(ttl=60 * 60, show_spinner=False)
def analyze_portfolio(holdings, sectors):
    """Run every risk calculation and return the results in one dictionary.

    Anything that can't be worked out (no price data, only one stock...) is None,
    and the rest is still filled in. Tickers with no price data are listed in
    "missing". Results are remembered for 1 hour.
    """
    result = {
        "weights": {},
        "sector_weights": {},
        "volatility": None,
        "beta": None,
        "correlation": None,
        "max_drawdown": None,
        "warnings": [],
        "missing": [],
    }

    # Step 1: only stocks we actually own
    owned = {}
    for ticker in holdings:
        if holdings[ticker] and holdings[ticker] > 0:
            owned[ticker] = holdings[ticker]
    if not owned:
        return result

    # Step 2: get a year of daily prices for our stocks plus SPY
    tickers = list(owned.keys())
    tickers.append(MARKET)
    prices = get_history_for_many(tickers, "1Y")

    # Note any of our stocks with no price data
    for ticker in owned:
        if prices.empty or ticker not in prices.columns:
            result["missing"].append(ticker)
    if prices.empty:
        return result

    # Step 3: weights from each stock's latest price
    latest_prices = {}
    for ticker in owned:
        if ticker in prices.columns:
            column = prices[ticker].dropna()
            if len(column) > 0:
                latest_prices[ticker] = float(column.iloc[-1])
    weights = portfolio_weights(owned, latest_prices)
    result["weights"] = weights
    result["sector_weights"] = sector_weights(weights, sectors)

    # Step 4: daily returns for our stocks (and SPY if we have it)
    columns = list(weights.keys())
    if MARKET in prices.columns and MARKET not in columns:
        columns.append(MARKET)
    returns = daily_returns(prices[columns])

    # Step 5: the risk numbers (each one is skipped if there isn't enough data)
    if len(returns) >= 2 and weights:
        result["volatility"] = portfolio_volatility(returns, weights)
        result["max_drawdown"] = max_drawdown(returns, weights)
        if MARKET in returns.columns:
            result["beta"] = portfolio_beta(returns, weights, returns[MARKET])
        result["correlation"] = correlation_matrix(returns)

    # Step 6: warnings
    result["warnings"] = risk_warnings(weights, result["sector_weights"], result["correlation"])
    return result
