import streamlit as st

from utils.state import get_tickers
from utils.ui import coming_soon, page_header

page_header("Daily Summary", "Here's what happened to your stocks today.")

coming_soon(
    "A short, friendly recap of your whole portfolio for today: which stocks went "
    "up or down, how much your portfolio changed in total, and the one or two news "
    "stories that mattered most, all written by Claude in plain English."
)

tickers = get_tickers()
if tickers:
    st.write("Stocks that will be included:", ", ".join(tickers))
else:
    st.caption("Add stocks on the **My Stocks** page to see them here.")
