import streamlit as st

from utils.ui import coming_soon, page_header

page_header("Ask StockSense", "Ask questions about your stocks in plain English.")

coming_soon(
    "A chat box where you can ask things like \"Why did Apple drop today?\" or "
    "\"Which of my stocks is riskiest?\" Claude will answer using your portfolio, "
    "prices and recent news."
)
