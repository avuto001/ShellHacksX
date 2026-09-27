# The app's starting point. Run it with: ./run.sh  (or: streamlit run app.py)
#
# This file only builds the sidebar and picks which page to show.
# Each page's code lives in its own file:
#   my_stocks.py           -> My Stocks (home)
#   pages/1_Stock_Detail.py ... pages/5_Goal_Benchmarking.py -> the other pages

import streamlit as st

from utils.ui import beginner_tip, sidebar_brand

# Every page in the sidebar, in order, with its icon (from fonts.google.com/icons)
PAGES = [
    st.Page("my_stocks.py", title="My Stocks", icon=":material/home:", default=True),
    st.Page("pages/1_Stock_Detail.py", title="Stock Detail", icon=":material/trending_up:"),
    st.Page("pages/2_Daily_Summary.py", title="Daily Summary", icon=":material/menu_book:"),
    st.Page("pages/3_Portfolio_Risk.py", title="Portfolio Risk", icon=":material/shield:"),
    st.Page("pages/4_Ask_StockSense.py", title="Ask StockSense", icon=":material/auto_awesome:"),
    st.Page("pages/5_Goal_Benchmarking.py", title="Goal Benchmarking", icon=":material/track_changes:"),
]

# Hide Streamlit's built-in menu so we can draw our own sidebar
current_page = st.navigation(PAGES, position="hidden")

# Sidebar: logo at the top, page links, then the beginner tip at the bottom
sidebar_brand()
for page in PAGES:
    st.sidebar.page_link(page)
beginner_tip()

# Show the chosen page
current_page.run()
