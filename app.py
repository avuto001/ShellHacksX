from html import escape as _escape

import streamlit as st

from services.stock_data import StockDataError, get_company_name, get_quote
from utils.price_history import get_price_history
from utils.state import add_stock, get_portfolio, remove_stock
from utils.ui import beginner_tip, change_color, page_header

page_header("My Portfolio", "Track your learning assets and performance")
beginner_tip()

# Colors come from .streamlit/config.toml, so this page follows the app's theme.
PRIMARY = st.get_option("theme.primaryColor") or "#3b82f6"
CARD = st.get_option("theme.secondaryBackgroundColor") or "#f0f2f6"

st.markdown(
    f"""
    <style>
    .ss-label {{opacity: .7; font-size: .75rem; text-transform: uppercase; letter-spacing: .03em;}}
    .ss-big {{font-size: 1.6rem; font-weight: 700;}}
    .ss-muted {{opacity: .7; font-size: .85rem;}}
    .ss-summary {{display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
                 border: 1px solid {PRIMARY}33; border-radius: 12px; padding: 16px 20px;
                 background: {CARD}66; margin-bottom: 1rem;}}
    .ss-summary > div {{flex: 1; min-width: 150px;}}
    .ss-card {{border: 1px solid {PRIMARY}33; border-radius: 12px; padding: 14px 16px;
              background: {CARD}66; height: 150px;}}
    .ss-card-top {{display: flex; justify-content: space-between; align-items: flex-start;}}
    .ss-ticker {{font-size: 1.15rem; font-weight: 700;}}
    .ss-pill {{border-radius: 6px; padding: 2px 8px; font-size: .75rem; font-weight: 600;}}
    .ss-card-bottom {{display: flex; justify-content: space-between; align-items: flex-end; margin-top: 14px;}}
    .ss-add {{border: 2px dashed {PRIMARY}44; border-radius: 12px; height: 150px; display: flex;
             flex-direction: column; align-items: center; justify-content: center; opacity: .75;}}
    </style>
    """,
    unsafe_allow_html=True,
)


def escape(text):
    """Make text safe for HTML, and stop Streamlit reading "$...$" as a math formula."""
    return _escape(str(text)).replace("$", "&#36;")


def sparkline(prices, color, width=110, height=36):
    """Draw a tiny line chart of `prices` as an SVG."""
    if len(prices) < 2:
        return ""
    low, high = min(prices), max(prices)
    spread = (high - low) or 1
    step = width / (len(prices) - 1)
    points = " ".join(
        f"{i * step:.1f},{height - 2 - (p - low) / spread * (height - 4):.1f}" for i, p in enumerate(prices)
    )
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2" '
        'stroke-linejoin="round" stroke-linecap="round"/></svg>'
    )


# --- Look up and add a stock ---
with st.form("add_stock", clear_on_submit=True):
    col1, col2, col3 = st.columns([4, 1, 1], vertical_alignment="bottom")
    ticker = col1.text_input(
        "Look up a stock", placeholder="🔍 Look up a stock by ticker (e.g. NVDA, AAPL)...",
        label_visibility="collapsed",
    )
    shares = col2.number_input("Shares", min_value=0.0, value=1.0, step=1.0, label_visibility="collapsed")
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

# --- Fetch every stock once ---
portfolio = get_portfolio()
stocks = []
for holding in portfolio:
    try:
        quote = get_quote(holding["ticker"])
        name = get_company_name(holding["ticker"])
    except StockDataError as e:
        st.error(f"{holding['ticker']}: {e}")
        continue
    stocks.append({**holding, "quote": quote, "name": name})

# --- Portfolio totals ---
total_value = sum(s["shares"] * s["quote"]["price"] for s in stocks)
day_change = sum(s["shares"] * (s["quote"]["change"] or 0) for s in stocks)
start_value = total_value - day_change
day_pct = day_change / start_value * 100 if start_value else 0
color = change_color(day_change)
arrow = "↗" if day_change > 0 else "↘" if day_change < 0 else "→"
sign = "+" if day_change >= 0 else "-"
count = len(stocks)

st.markdown(
    f'<div class="ss-summary">'
    f'<div><div class="ss-muted">Total Portfolio Value</div><div class="ss-big">&#36;{total_value:,.2f}</div></div>'
    f'<div style="text-align:center;"><div class="ss-muted">Total Daily Change</div>'
    f'<div class="ss-big" style="color:{color};">{arrow} {sign}&#36;{abs(day_change):,.2f} ({day_pct:+.2f}%)</div></div>'
    f'<div style="text-align:right;"><div class="ss-muted">Holdings Size</div>'
    f'<div class="ss-big">{count} {"Company" if count == 1 else "Companies"}</div></div>'
    f"</div>",
    unsafe_allow_html=True,
)

# --- Stock cards ---
st.markdown("#### Your Monitored Stocks")
if not stocks:
    st.info("Your portfolio is empty. Look up a ticker above to get started.")

columns = st.columns(3)
for i, stock in enumerate(stocks):
    pct = stock["quote"]["percent_change"] or 0
    color = change_color(pct)
    prices = [price for _, price in get_price_history(stock["ticker"], "1M")]
    with columns[i % 3]:
        st.markdown(
            f'<div class="ss-card">'
            f'<div class="ss-card-top"><div><div class="ss-ticker">{escape(stock["ticker"])}</div>'
            f'<div class="ss-muted">{escape(stock["name"] or "")}</div></div>'
            f'<span class="ss-pill" style="color:{color}; background:{color}22;">{pct:+.2f}%</span></div>'
            f'<div class="ss-card-bottom"><div><div class="ss-label">Current price</div>'
            f'<div class="ss-big">&#36;{stock["quote"]["price"]:,.2f}</div></div>'
            f"{sparkline(prices, color)}</div></div>",
            unsafe_allow_html=True,
        )
        worth = stock["shares"] * stock["quote"]["price"]
        info, remove = st.columns([3, 1], vertical_alignment="center")
        info.caption(f"{stock['shares']:g} shares · \\${worth:,.2f}")
        if remove.button("Remove", key=f"remove_{stock['ticker']}", type="tertiary"):
            remove_stock(stock["ticker"])
            st.rerun()

with columns[len(stocks) % 3]:
    st.markdown(
        '<div class="ss-add"><div style="font-size:1.6rem;">+</div>'
        "<div>Monitor another asset</div>"
        '<div class="ss-muted">Use the search box above</div></div>',
        unsafe_allow_html=True,
    )

if stocks:
    st.caption("Open **Stock Detail** in the sidebar to see news for each stock.")
