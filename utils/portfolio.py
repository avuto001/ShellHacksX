"""Gathers everything the AI needs about the portfolio, in the format
services/ai_summary.py expects."""

import streamlit as st

from services.news_cleaner import clean_news
from services.stock_data import StockDataError, _get, get_company_name, get_news, get_quote
from utils.state import get_portfolio


@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)
def get_industry(ticker):
    """Return the company's industry (e.g. "Technology"), or None if Finnhub doesn't know it."""
    try:
        return _get("stock/profile2", {"symbol": ticker.upper()}).get("finnhubIndustry") or None
    except StockDataError:
        return None


def load_portfolio_data():
    """Return (stocks, problems).

    stocks:   one dict per stock, like {"ticker", "name", "shares", "quote", "news"},
              where "news" is the cleaned, numbered list from clean_news().
    problems: "TICKER: reason" messages for stocks Finnhub couldn't load.
    """
    stocks = []
    problems = []
    for holding in get_portfolio():
        ticker = holding["ticker"]
        try:
            name = get_company_name(ticker)
            stocks.append({
                "ticker": ticker,
                "name": name,
                "shares": holding["shares"],
                "quote": get_quote(ticker),
                "news": clean_news(get_news(ticker), ticker, name),
            })
        except StockDataError as e:
            problems.append(f"{ticker}: {e}")
    return stocks, problems
