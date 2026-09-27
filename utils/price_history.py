"""Price history for charts, from Yahoo Finance (no API key needed).

Finnhub's free plan doesn't include past prices, so the charts use Yahoo instead.
"""

from datetime import datetime

import requests
import streamlit as st

# Chart buttons -> (Yahoo range, Yahoo interval)
PERIODS = {
    "1D": ("1d", "5m"),
    "5D": ("5d", "30m"),
    "1M": ("1mo", "1d"),
    "YTD": ("ytd", "1d"),
    "1Y": ("1y", "1d"),
}


@st.cache_data(ttl=5 * 60, show_spinner=False)
def get_price_history(ticker, period="1M"):
    """Return [(time, close price), ...] for the chart, or [] if Yahoo has no data."""
    yahoo_range, interval = PERIODS[period]
    try:
        response = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
            params={"range": yahoo_range, "interval": interval},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()["chart"]["result"][0]
        times = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        return []
    return [(datetime.fromtimestamp(t), c) for t, c in zip(times, closes) if c is not None]
