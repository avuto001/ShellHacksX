import streamlit as st

from utils.state import get_portfolio
from utils.ui import coming_soon, page_header

page_header("Portfolio Risk", "How risky is your portfolio, in numbers and charts.")

coming_soon(
    "Risk numbers with simple explanations: how concentrated your portfolio is in a "
    "few stocks, how much prices swing (volatility), how closely you follow the market "
    "(beta), which stocks move together (correlation) and your biggest drop from a "
    "peak (drawdown). Charts will show each one."
)

portfolio = get_portfolio()
if portfolio:
    st.write("Your holdings:")
    st.dataframe(portfolio, hide_index=True)
else:
    st.caption("Add stocks on the **My Stocks** page to see them here.")
