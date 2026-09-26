"""The shared portfolio list, stored in st.session_state.

Every page imports these functions so they all see the same list of stocks.
Note: session_state lives only while the browser tab is open. Refreshing the
page starts with an empty portfolio again.
"""

import streamlit as st

_KEY = "portfolio"


def _init():
    if _KEY not in st.session_state:
        st.session_state[_KEY] = []


def get_portfolio():
    """Return the portfolio as a list of dicts like {"ticker": "AAPL", "shares": 10.0}."""
    _init()
    return st.session_state[_KEY]


def get_tickers():
    """Return just the ticker symbols, e.g. ["AAPL", "MSFT"]."""
    return [holding["ticker"] for holding in get_portfolio()]


def add_stock(ticker, shares=1.0):
    """Add a stock, or update its share count if it's already in the portfolio."""
    ticker = ticker.strip().upper()
    for holding in get_portfolio():
        if holding["ticker"] == ticker:
            holding["shares"] = shares
            return
    get_portfolio().append({"ticker": ticker, "shares": shares})


def remove_stock(ticker):
    """Remove a stock from the portfolio. Does nothing if it isn't there."""
    ticker = ticker.strip().upper()
    st.session_state[_KEY] = [h for h in get_portfolio() if h["ticker"] != ticker]
