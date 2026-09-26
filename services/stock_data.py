"""Helpers for fetching stock data from the Finnhub API."""

from datetime import date, timedelta

import requests
import streamlit as st

BASE_URL = "https://finnhub.io/api/v1"


class StockDataError(Exception):
    """Raised when Finnhub can't give us usable data."""


def _get(endpoint, params):
    """Call a Finnhub endpoint and return the JSON response."""
    params = {**params, "token": st.secrets["FINNHUB_API_KEY"]}
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=10)
    except requests.RequestException as e:
        raise StockDataError(f"Couldn't reach Finnhub: {e}") from e

    if response.status_code == 401:
        raise StockDataError("Finnhub rejected the API key. Check FINNHUB_API_KEY in .streamlit/secrets.toml.")
    if response.status_code == 429:
        raise StockDataError("Too many requests to Finnhub. Wait a minute and try again.")
    if not response.ok:
        raise StockDataError(f"Finnhub returned an error ({response.status_code}).")
    return response.json()


@st.cache_data(ttl=60)
def get_quote(ticker):
    """Return the current price and today's change for a ticker."""
    data = _get("quote", {"symbol": ticker.upper()})
    # Finnhub returns all zeros for unknown tickers instead of an error.
    if not data or data.get("c") in (None, 0):
        raise StockDataError(f"No price found for '{ticker.upper()}'. Is the ticker correct?")
    return {
        "price": data["c"],
        "change": data["d"],
        "percent_change": data["dp"],
        "previous_close": data["pc"],
    }


@st.cache_data(ttl=24 * 60 * 60)
def get_company_name(ticker):
    """Return the company's name, or None if Finnhub doesn't know it."""
    data = _get("stock/profile2", {"symbol": ticker.upper()})
    return data.get("name") or None


@st.cache_data(ttl=15 * 60)
def get_news(ticker, limit=10):
    """Return up to `limit` news headlines from the past week, newest first."""
    today = date.today()
    week_ago = today - timedelta(days=7)
    articles = _get(
        "company-news",
        {"symbol": ticker.upper(), "from": week_ago.isoformat(), "to": today.isoformat()},
    )
    articles = sorted(articles, key=lambda a: a.get("datetime", 0), reverse=True)
    return [
        {
            "headline": a["headline"],
            "url": a["url"],
            "source": a.get("source", ""),
            "datetime": a.get("datetime", 0),
        }
        for a in articles
        if a.get("headline") and a.get("url")
    ][:limit]
