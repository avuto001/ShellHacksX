"""Shared display pieces so every page looks the same."""

import random
import re
from html import escape

import streamlit as st

# App colors (the dark theme itself lives in .streamlit/config.toml)
GREEN = "#3DAA7A"
RED = "#E05252"
GRAY = "#6B7280"
BLUE = "#3B6FE0"
ORANGE = "#E0A33B"
CARD_BACKGROUND = "#121A2B"
CARD_BORDER = "#1F2A3D"
MUTED_TEXT = "#8B93A7"

BEGINNER_TIPS = [
    "Diversification means spreading money across different stocks to reduce risk.",
    "A single day's move rarely matters much for a long-term investor.",
    "Good news can be \"priced in\": the stock may not move if everyone expected it.",
    "Owning stocks from different industries lowers the risk of one bad headline.",
    "Big companies usually move less day to day than small, fast-growing ones.",
    "A stock's price alone doesn't tell you if it's cheap or expensive.",
]

STYLES = f"""
<style>
/* Sidebar */
[data-testid="stSidebar"] {{
    background-color: #0E1420;
    border-right: 1px solid {CARD_BORDER};
}}
.ss-brand {{ display: flex; align-items: center; gap: 10px; margin: 4px 0 18px 0; }}
.ss-brand-icon {{ background: {BLUE}; color: white; border-radius: 8px; width: 34px; height: 34px;
                  display: flex; align-items: center; justify-content: center; font-size: 1.1rem; }}
.ss-brand-name {{ font-weight: 700; font-size: 1.1rem; line-height: 1.1; }}
.ss-brand-caption {{ color: {MUTED_TEXT}; font-size: .65rem; letter-spacing: .12em; font-weight: 600; }}

/* Cards: plain HTML ones (.ss-card) and Streamlit containers made with card() */
.ss-card, div[class*="st-key-ss-card"] {{
    background: {CARD_BACKGROUND};
    border: 1px solid {CARD_BORDER};
    border-radius: 12px;
    padding: 20px;
}}
.ss-card-title {{ font-weight: 700; font-size: 1rem; margin-bottom: 8px; }}

/* Metric cards */
.ss-metric {{ height: 100%; }}
.ss-metric-label {{ color: {MUTED_TEXT}; font-size: .72rem; font-weight: 600;
                    text-transform: uppercase; letter-spacing: .06em; }}
.ss-metric-value {{ color: #FFFFFF; font-size: 1.9rem; font-weight: 700; margin: 6px 0 4px 0; }}
.ss-metric-desc {{ color: {MUTED_TEXT}; font-size: .82rem; }}

/* Tables */
.ss-table {{ width: 100%; border-collapse: collapse; font-size: .9rem; }}
.ss-table th {{ background: #0E1420; color: {MUTED_TEXT}; font-size: .72rem; font-weight: 600;
                text-transform: uppercase; letter-spacing: .05em; text-align: left; padding: 10px 12px; }}
.ss-table td {{ padding: 11px 12px; border-top: 1px solid {CARD_BORDER}; }}
.ss-table .ss-num {{ text-align: right; }}
.ss-pos {{ color: {GREEN}; font-weight: 600; }}
.ss-neg {{ color: {RED}; font-weight: 600; }}

/* Warning and "all clear" cards */
.ss-alert {{ background: {CARD_BACKGROUND}; border: 1px solid {CARD_BORDER}; border-radius: 12px;
             padding: 14px 18px; margin-bottom: 10px; }}
.ss-alert-warn {{ border-left: 4px solid {ORANGE}; }}
.ss-alert-ok {{ border-left: 4px solid {GREEN}; color: {GREEN}; font-weight: 600; }}
</style>
"""


def change_color(value):
    """Return green for gains, red for losses, gray for no change."""
    if value > 0:
        return GREEN
    if value < 0:
        return RED
    return GRAY


def html_text(text):
    """Make text safe to put inside HTML, and stop Streamlit reading "$...$" as a math formula."""
    return escape(str(text)).replace("$", "&#36;")


def link_citations(html, articles):
    """Turn each [n] in AI text (already passed through html_text) into a small link to article n.

    `articles` is the numbered list the AI was given; each has an "id" and a "url".
    """
    urls = {article["id"]: article["url"] for article in articles}

    def to_link(match):
        url = urls.get(int(match.group(1)))
        if not url:
            return match.group(0)
        return (
            f'<a href="{html_text(url)}" target="_blank" style="font-size:.75rem; font-weight:600; '
            f'text-decoration:none; vertical-align:super;">[{match.group(1)}]</a>'
        )

    return re.sub(r"\[(\d+)\]", to_link, html)


def page_header(title, subtitle=None):
    """Set up the page and show its title. Call this first on every page."""
    st.set_page_config(page_title=f"{title} · StockSense", page_icon=":material/trending_up:")
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def apply_styles():
    """Add the app's shared CSS (cards, metric cards, sidebar, tables). Call at the top of every page."""
    st.markdown(STYLES, unsafe_allow_html=True)


def sidebar_brand():
    """The "StockSense / FINANCIAL LITERACY" logo at the top of the sidebar."""
    st.sidebar.markdown(
        '<div class="ss-brand"><div class="ss-brand-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg></div>'
        '<div><div class="ss-brand-name">StockSense</div>'
        '<div class="ss-brand-caption">FINANCIAL LITERACY</div></div></div>',
        unsafe_allow_html=True,
    )


def beginner_tip():
    """Show one random beginner tip in a card at the bottom of the sidebar.

    The tip is picked once per visit, so it doesn't change on every click.
    """
    if "beginner_tip" not in st.session_state:
        st.session_state["beginner_tip"] = random.choice(BEGINNER_TIPS)
    with st.sidebar.container(border=True):
        st.markdown(":material/lightbulb: **Beginner Tip**")
        st.caption(st.session_state["beginner_tip"])


def card(key):
    """A card-styled container. Use it like:  with card("chart"): st.plotly_chart(...)

    `key` must be unique on the page (letters, numbers, - and _).
    """
    return st.container(key=f"ss-card-{key}")


def metric_card(label, value, description):
    """One number card: small gray LABEL, big white number, short gray description."""
    st.markdown(
        f'<div class="ss-card ss-metric"><div class="ss-metric-label">{html_text(label)}</div>'
        f'<div class="ss-metric-value">{html_text(value)}</div>'
        f'<div class="ss-metric-desc">{html_text(description)}</div></div>',
        unsafe_allow_html=True,
    )


def coming_soon(description):
    """Show a note explaining what a page will do once it's built."""
    st.info(f"**Coming soon.** {description}")


def stock_card(ticker, name, quote, shares=None):
    """Show one stock's name, price and today's change in a bordered box.

    `quote` is the dict returned by services.stock_data.get_quote().
    """
    with st.container(border=True):
        st.metric(
            label=f"{name} ({ticker})" if name else ticker,
            value=f"${quote['price']:,.2f}",
            delta=f"{quote['change']:+.2f} ({quote['percent_change']:+.2f}%)",
        )
        if shares is not None:
            st.caption(f"{shares:g} shares · worth ${shares * quote['price']:,.2f}")
