import streamlit as st

from services.stock_data import StockDataError, get_company_name, get_quote
from utils.state import add_stock, get_portfolio, remove_stock
from utils.ui import page_header, stock_card

page_header("My Stocks", "StockSense – Make sense of your stocks.")

# --- Add a stock ---
with st.form("add_stock", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 1, 1], vertical_alignment="bottom")
    ticker = col1.text_input("Ticker symbol", placeholder="e.g. AAPL")
    shares = col2.number_input("Shares", min_value=0.0, value=1.0, step=1.0)
    submitted = col3.form_submit_button("Add", width="stretch")

if submitted and ticker.strip():
    ticker = ticker.strip().upper()
    try:
        get_quote(ticker)  # make sure the ticker is real before adding it
    except StockDataError as e:
        st.error(str(e))
    else:
        add_stock(ticker, shares)
        st.success(f"Added {ticker}.")

# --- Show the portfolio ---
portfolio = get_portfolio()
if not portfolio:
    st.info("Your portfolio is empty. Add a ticker above to get started.")

for holding in portfolio:
    ticker = holding["ticker"]
    try:
        quote = get_quote(ticker)
        name = get_company_name(ticker)
    except StockDataError as e:
        st.error(f"{ticker}: {e}")
        continue

    col1, col2 = st.columns([5, 1], vertical_alignment="center")
    with col1:
        stock_card(ticker, name, quote, holding["shares"])
    if col2.button("Remove", key=f"remove_{ticker}"):
        remove_stock(ticker)
        st.rerun()

if portfolio:
    st.caption("Open **Stock Detail** in the sidebar to see news for each stock.")
