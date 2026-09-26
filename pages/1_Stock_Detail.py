from datetime import datetime

import streamlit as st

from services.ai_summary import summarize_news
from services.stock_data import StockDataError, get_company_name, get_news, get_quote
from utils.state import get_tickers
from utils.ui import coming_soon, page_header, stock_card

page_header("Stock Detail", "Price, news and an AI summary for one stock.")

tickers = get_tickers()
if not tickers:
    st.info("Add stocks on the **My Stocks** page first.")
    st.stop()

ticker = st.selectbox("Choose a stock", tickers)

try:
    quote = get_quote(ticker)
    name = get_company_name(ticker)
    news = get_news(ticker)
except StockDataError as e:
    st.error(str(e))
    st.stop()

stock_card(ticker, name, quote)

st.subheader("AI summary")
coming_soon(
    "Claude will read this week's headlines and explain in plain English what's "
    "going on with the company and whether the news looks good or bad."
)
summary = summarize_news(ticker, news)
if summary:
    st.write(summary)

st.subheader("Headlines from the past week")
if not news:
    st.info("No news found for this stock in the past week.")
for article in news:
    when = datetime.fromtimestamp(article["datetime"]).strftime("%b %d")
    st.markdown(f"- [{article['headline']}]({article['url']}) — {article['source']}, {when}")
