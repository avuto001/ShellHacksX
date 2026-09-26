"""Sends stock news to Claude and gets back plain-English summaries.

Every function here returns an empty string for now, so pages can call them
without crashing. Fill them in one at a time.
"""

import anthropic
import streamlit as st

from services.security import clean_news_text

MODEL = "claude-opus-5"


def _get_client():
    """Create a Claude client using the key from .streamlit/secrets.toml."""
    return anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])


def summarize_news(ticker, articles):
    """Summarize one stock's recent news in a few plain-English sentences.

    Inputs:
        ticker:   the stock symbol, e.g. "AAPL"
        articles: the list returned by services.stock_data.get_news(), where each
                  item has "headline", "url", "source" and "datetime"
    Output:
        A short summary string (3-5 sentences) that a beginner investor can
        understand, or "" if there's nothing to summarize.

    What to build:
        1. Run every headline through clean_news_text() from services/security.py.
        2. Put the cleaned headlines into a prompt asking Claude for a short summary
           and whether the news looks good, bad or neutral for the stock.
        3. Call _get_client().messages.create(model=MODEL, ...) and return the text.
        4. Add @st.cache_data(ttl=15 * 60) above the function so repeated views
           don't cost money.
    """
    # TODO: build this (see the steps in the docstring above)
    return ""


def summarize_portfolio_day(portfolio_data):
    """Write a friendly "here's what happened today" recap of the whole portfolio.

    Inputs:
        portfolio_data: a list of dicts, one per stock, like
            {"ticker": "AAPL", "name": "Apple Inc", "shares": 10,
             "quote": <dict from get_quote()>, "news": <list from get_news()>}
    Output:
        A few short paragraphs covering the biggest movers, the total change in
        value and the most important news, or "" if the portfolio is empty.

    What to build:
        Same idea as summarize_news(), but with every stock in one prompt.
        Clean all news text with clean_news_text() before sending it.
    """
    # TODO: build this
    return ""


def answer_question(question, portfolio_data, history=None):
    """Answer a user's question about their stocks (used by Ask StockSense).

    Inputs:
        question:       what the user typed, e.g. "Why did Apple drop today?"
        portfolio_data: same format as in summarize_portfolio_day()
        history:        earlier chat messages as a list of
                        {"role": "user" or "assistant", "content": "..."}; may be None
    Output:
        Claude's answer as a string.

    What to build:
        Give Claude the portfolio data (with news cleaned by clean_news_text())
        plus the chat history, and ask it to answer only from that data. It should
        say so when it doesn't know, and never give "buy this stock" advice.
    """
    # TODO: build this
    return ""
