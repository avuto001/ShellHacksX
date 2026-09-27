# Past prices for risk math, as a pandas table.
#
# The prices come from Yahoo Finance through utils/price_history.py (the same
# free source the charts use), so no extra library or API key is needed.

import pandas as pd

from utils.price_history import get_price_history


def get_history_for_many(tickers, period="1Y"):
    """Return daily closing prices for several tickers as one table.

    Input:
        tickers: a list like ["AAPL", "MSFT", "SPY"]
        period:  how far back to go (see PERIODS in utils/price_history.py)
    Output:
        A pandas DataFrame with one row per day and one column per ticker.
        Tickers Yahoo has no data for are left out. If there's no data at all,
        returns an empty DataFrame.
    """
    columns = {}

    for ticker in tickers:
        # Get [(time, price), ...] for this ticker
        history = get_price_history(ticker, period)
        if not history:
            continue

        # Split it into a list of dates and a list of prices
        dates = []
        prices = []
        for when, price in history:
            dates.append(pd.Timestamp(when.date()))
            prices.append(price)

        # Make it a pandas Series (a list of prices labeled by date)
        series = pd.Series(prices, index=dates)
        # If a day appears twice, keep the last price for that day
        series = series[~series.index.duplicated(keep="last")]
        columns[ticker] = series

    if not columns:
        return pd.DataFrame()

    # Line the tickers up side by side by date
    table = pd.DataFrame(columns)
    return table.sort_index()
