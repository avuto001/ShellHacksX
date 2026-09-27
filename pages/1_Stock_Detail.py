# This file is the Stock Detail page
import re
import time
from html import escape as _escape

import altair as alt
import streamlit as st

from services.ai_summary import summarize_stock
from services.news_cleaner import clean_news
from services.stock_data import StockDataError, _get, get_company_name, get_news, get_quote
from utils.price_history import PERIODS, get_price_history
from utils.state import get_tickers
from utils.ui import GREEN, RED, beginner_tip, change_color, page_header

page_header("Stock Detail", "Price, news and an AI summary for one stock.")
beginner_tip()

SENTIMENTS = {
    "positive": ("🟢", "News looks positive", GREEN),
    "negative": ("🔴", "News looks negative", RED),
    "neutral": ("⚪", "News looks neutral", "#6b7280"),
}

# Shown when the AI summary doesn't include its own beginner term
BEGINNER_INSIGHTS = [
    '"Defensive stocks" tend to hold value during market dips.',
    "A single day's move rarely matters much for a long-term investor.",
    "Good news can be \"priced in\": the stock may not move if everyone expected it.",
    "Owning stocks from different industries lowers the risk of one bad headline.",
    "Big companies usually move less day to day than small, fast-growing ones.",
]

# Colors come from .streamlit/config.toml, so this page follows the app's theme.
PRIMARY = st.get_option("theme.primaryColor") or "#3b82f6"
CARD = st.get_option("theme.secondaryBackgroundColor") or "#f0f2f6"

st.markdown(
    f"""
    <style>
    .ss-badge {{background: {PRIMARY}22; color: {PRIMARY}; border-radius: 6px;
               padding: 2px 8px; font-size: .75rem; margin-left: .5rem; vertical-align: middle;}}
    .ss-ticker {{font-size: 1.8rem; font-weight: 700;}}
    .ss-muted {{opacity: .7; font-size: .85rem;}}
    .ss-price {{font-size: 2.2rem; font-weight: 700; text-align: right; line-height: 1.1;}}
    .ss-pill {{border-radius: 6px; padding: 3px 10px; font-size: .85rem; font-weight: 600;
              margin-left: .5rem; vertical-align: middle;}}
    .ss-news {{border: 1px solid {PRIMARY}33; border-radius: 10px; padding: 12px 14px;
              margin-bottom: 10px; background: {CARD}66;}}
    .ss-news a {{color: inherit; text-decoration: none; font-weight: 600;}}
    .ss-news a:hover {{text-decoration: underline;}}
    .ss-source {{color: {PRIMARY}; font-weight: 600;}}
    .ss-summary {{border: 1px solid {PRIMARY}88; border-radius: 12px; padding: 16px 18px;
                 background: {CARD}66; line-height: 1.6;}}
    .ss-insight {{background: {PRIMARY}14; border-radius: 8px; padding: 10px 12px;
                 margin-top: 12px; font-size: .9rem;}}
    .ss-num {{color: {PRIMARY}; font-weight: 700; margin-right: 4px;}}
    .ss-cite {{color: {PRIMARY}; font-size: .75rem; font-weight: 600; text-decoration: none;
              vertical-align: super;}}
    .ss-sentiment {{display: inline-block; border-radius: 6px; padding: 2px 10px; font-size: .8rem;
                   font-weight: 600; margin-bottom: 8px;}}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)
def get_industry(ticker):
    """Return the company's industry (e.g. "Technology"), or None if Finnhub doesn't know it."""
    try:
        return _get("stock/profile2", {"symbol": ticker.upper()}).get("finnhubIndustry") or None
    except StockDataError:
        return None


def escape(text):
    """Make text safe for HTML, and stop Streamlit reading "$...$" as a math formula."""
    return _escape(str(text)).replace("$", "&#36;")


def link_citations(text, articles):
    """Turn each [n] in the summary into a small link to article n."""
    urls = {a["id"]: a["url"] for a in articles}

    def to_link(match):
        url = urls.get(int(match.group(1)))
        if not url:
            return match.group(0)
        return f'<a class="ss-cite" href="{escape(url)}" target="_blank">[{match.group(1)}]</a>'

    return re.sub(r"\[(\d+)\]", to_link, text)


def time_ago(timestamp):
    """Turn a Unix timestamp into '2 hours ago' style text."""
    seconds = max(0, time.time() - timestamp)
    for unit, size in (("day", 86400), ("hour", 3600), ("minute", 60)):
        if seconds >= size:
            count = int(seconds // size)
            return f"{count} {unit}{'s' if count != 1 else ''} ago"
    return "just now"


#Ty is doing the My stocks (my portfolio) from the Figma
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

industry = get_industry(ticker)
articles = clean_news(news, ticker, name)  # no repeats, numbered so the AI can cite them

# --- Header: ticker, company, price ---
pct = quote["percent_change"] or 0
color = change_color(pct)
arrow = "↗" if pct > 0 else "↘" if pct < 0 else "→"
badge = f'<span class="ss-badge">{escape(industry)}</span>' if industry else ""

left, right = st.columns([3, 2], vertical_alignment="center")
left.markdown(
    f'<div class="ss-ticker">{escape(ticker)}{badge}</div>'
    f'<div class="ss-muted">{escape(name or "")}</div>',
    unsafe_allow_html=True,
)
right.markdown(
    f'<div class="ss-price">&#36;{quote["price"]:,.2f}'
    f'<span class="ss-pill" style="color:{color}; background:{color}22;">{arrow} {pct:+.2f}%</span></div>'
    '<div class="ss-muted" style="text-align:right;">USD • Live Market Quote</div>',
    unsafe_allow_html=True,
)

# --- Price chart ---
with st.container(border=True):
    title_col, period_col = st.columns([3, 2], vertical_alignment="center")
    period = period_col.segmented_control(
        "Time period", list(PERIODS), default="1M", key="chart_period", label_visibility="collapsed"
    ) or "1M"
    title_col.markdown(f"**{period} Historical Performance**")

    history = get_price_history(ticker, period)
    if history:
        line_color = GREEN if history[-1][1] >= history[0][1] else RED
        chart = (
            alt.Chart(alt.Data(values=[{"time": t.isoformat(), "price": p} for t, p in history]))
            .mark_line(color=line_color, strokeWidth=2)
            .encode(
                x=alt.X("time:T", title=None),
                y=alt.Y("price:Q", title=None, scale=alt.Scale(zero=False), axis=alt.Axis(format="$,.2f")),
                tooltip=[alt.Tooltip("time:T", title="Time"), alt.Tooltip("price:Q", title="Price", format="$,.2f")],
            )
            .properties(height=260)
        )
        st.altair_chart(chart, width="stretch")
    else:
        st.caption("Price history isn't available for this stock right now.")

# --- News and AI summary side by side ---
news_col, summary_col = st.columns(2, gap="large")

with news_col:
    st.markdown("#### Latest News Headlines")
    if not articles:
        st.info("No news found for this stock in the past week.")
    for article in articles:
        st.markdown(
            f'<div class="ss-news"><span class="ss-num">[{article["id"]}]</span>'
            f'<a href="{escape(article["url"])}" target="_blank">{escape(article["headline"])}</a><br>'
            f'<span class="ss-muted"><span class="ss-source">{escape(article["source"])}</span>'
            f' • {time_ago(article["datetime"])}</span></div>',
            unsafe_allow_html=True,
        )

with summary_col:
    st.markdown("#### ✨ AI Plain-English Summary")
    with st.spinner("Claude is reading the news..."):
        result = summarize_stock(ticker, name, articles, quote)

    if result["available"]:
        icon, label, sentiment_color = SENTIMENTS.get(result["sentiment"], SENTIMENTS["neutral"])
        sentiment = (
            f'<span class="ss-sentiment" style="color:{sentiment_color}; background:{sentiment_color}22;">'
            f"{icon} {label}</span>"
        )
        body = f"<p>{link_citations(escape(result['summary']), articles)}</p>"
    else:
        sentiment = ""
        body = f'<p class="ss-muted">{escape(result["summary"])}</p>'

    if result["insight_term"] and result["insight_text"]:
        insight = f"<b>{escape(result['insight_term'])}:</b> {escape(result['insight_text'])}"
    else:
        insight = escape(BEGINNER_INSIGHTS[sum(map(ord, ticker)) % len(BEGINNER_INSIGHTS)])

    st.markdown(
        f'<div class="ss-summary">{sentiment}{body}'
        f'<div class="ss-insight">ⓘ <b>Beginner Insight:</b> {insight}</div></div>',
        unsafe_allow_html=True,
    )
    st.caption("AI explanation of the news, not financial advice. Numbers like [1] link to the article it came from.")
