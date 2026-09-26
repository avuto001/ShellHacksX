from datetime import datetime

import streamlit as st

from services.stock_data import StockDataError, get_company_name, get_news, get_quote

st.set_page_config(page_title="StockSense", page_icon="📈")

st.title("StockSense")
st.subheader("StockSense – Make sense of your stocks.")

st.divider()

# --- Quick test section ---
st.header("Quick test")
ticker = st.text_input("Enter a ticker symbol", placeholder="e.g. AAPL").strip().upper()

if ticker:
    try:
        with st.spinner(f"Looking up {ticker}..."):
            quote = get_quote(ticker)
            name = get_company_name(ticker)
            news = get_news(ticker)
    except StockDataError as e:
        st.error(str(e))
    else:
        st.metric(
            label=name or ticker,
            value=f"${quote['price']:,.2f}",
            delta=f"{quote['change']:+.2f} ({quote['percent_change']:+.2f}%)",
        )

        st.subheader("Headlines from the past week")
        if not news:
            st.info("No news found for this ticker in the past week.")
        for article in news:
            when = datetime.fromtimestamp(article["datetime"]).strftime("%b %d")
            st.markdown(f"- [{article['headline']}]({article['url']}) — {article['source']}, {when}")
