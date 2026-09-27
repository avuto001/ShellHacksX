import streamlit as st

from services.ai_summary import summarize_portfolio_day
from utils.portfolio import load_portfolio_data
from utils.state import get_tickers
from utils.ui import apply_styles, change_color, link_citations, page_header
from utils.ui import html_text as escape

page_header("Daily Summary", "Here's what happened to your stocks today.")
apply_styles()

# Colors come from .streamlit/config.toml, so this page follows the app's theme.
PRIMARY = st.get_option("theme.primaryColor") or "#3b82f6"
CARD = st.get_option("theme.secondaryBackgroundColor") or "#f0f2f6"

st.markdown(
    f"""
    <style>
    .ss-recap {{border: 1px solid {PRIMARY}88; border-radius: 12px; padding: 16px 18px;
               background: {CARD}66; line-height: 1.6;}}
    .ss-muted {{opacity: .7; font-size: .85rem;}}
    .ss-row {{display: flex; justify-content: space-between; align-items: center;
             border-bottom: 1px solid {PRIMARY}22; padding: 8px 0;}}
    .ss-pill {{border-radius: 6px; padding: 2px 8px; font-size: .8rem; font-weight: 600;}}
    </style>
    """,
    unsafe_allow_html=True,
)

# This is stock details
tickers = get_tickers()
if not tickers:
    st.info("Add stocks on the **My Stocks** page to see your daily summary here.")
    st.stop()

with st.spinner("Claude is reading today's news for your stocks..."):
    stocks, problems = load_portfolio_data()
    result = summarize_portfolio_day(stocks)

for problem in problems:
    st.error(problem)

# --- Today's totals (worked out here, not by the AI) ---
total_value = sum(s["shares"] * s["quote"]["price"] for s in stocks)
day_change = sum(s["shares"] * (s["quote"]["change"] or 0) for s in stocks)
start_value = total_value - day_change
day_pct = day_change / start_value * 100 if start_value else 0

col1, col2, col3 = st.columns(3)
col1.metric("Portfolio value", f"${total_value:,.2f}", border=True)
sign = "+" if day_change >= 0 else "-"
col2.metric("Today's change", f"{sign}${abs(day_change):,.2f}", f"{day_pct:+.2f}%", border=True)
col3.metric("Stocks", len(stocks), border=True)

# --- AI recap and today's movers side by side ---
recap_col, movers_col = st.columns([3, 2], gap="large")

with recap_col:
    st.markdown("#### Today's recap")
    if result["available"]:
        body = link_citations(escape(result["summary"]), result["articles"])
    else:
        body = f'<span class="ss-muted">{escape(result["summary"])}</span>'
    st.markdown(f'<div class="ss-recap">{body}</div>', unsafe_allow_html=True)

    # The articles the recap is based on, so readers can check it
    cited = [a for a in result["articles"] if a["id"] in result["citations"]]
    if cited:
        with st.expander("Sources", icon=":material/article:"):
            for article in cited:
                st.markdown(
                    f'[{article["id"]}] **{escape(article["ticker"])}** · '
                    f'<a href="{escape(article["url"])}" target="_blank">{escape(article["headline"])}</a> '
                    f'<span class="ss-muted">({escape(article.get("source", ""))})</span>',
                    unsafe_allow_html=True,
                )

with movers_col:
    st.markdown("#### Today's movers")
    by_move = sorted(stocks, key=lambda s: s["quote"]["percent_change"] or 0, reverse=True)
    rows = ""
    for stock in by_move:
        pct = stock["quote"]["percent_change"] or 0
        color = change_color(pct)
        rows += (
            f'<div class="ss-row"><div><b>{escape(stock["ticker"])}</b><br>'
            f'<span class="ss-muted">{escape(stock["name"] or "")}</span></div>'
            f'<span class="ss-pill" style="color:{color}; background:{color}22;">{pct:+.2f}%</span></div>'
        )
    st.markdown(rows, unsafe_allow_html=True)

st.caption("AI explanation of the news, not financial advice. Numbers like [1] link to the article it came from.")
