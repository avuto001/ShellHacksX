"""Shared display pieces so every page looks the same."""

import re
from html import escape

import streamlit as st

GREEN = "#16a34a"
RED = "#dc2626"
GRAY = "#6b7280"


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
    st.set_page_config(page_title=f"{title} · StockSense", page_icon="📈")
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def beginner_tip():
    """Show a short investing tip in the sidebar."""
    with st.sidebar.container(border=True):
        st.markdown("💡 **Beginner Tip**")
        st.caption("Diversification means spreading money across different stocks to reduce risk.")


def coming_soon(description):
    """Show a note explaining what a page will do once it's built."""
    st.info(f"🚧 **Coming soon.** {description}")


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
