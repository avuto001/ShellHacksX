# This file is the Portfolio Risk page
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.price_history import get_history_for_many
from services.risk import MARKET, TRADING_DAYS_PER_YEAR, analyze_portfolio, daily_returns
from services.stock_data import StockDataError, get_quote
from utils.portfolio import get_industry
from utils.state import get_portfolio
from utils.ui import BLUE, GRAY, GREEN, ORANGE, RED, apply_styles, card, metric_card, page_header
from utils.ui import html_text as escape

page_header("Portfolio Risk Health", "Understand volatility and safety metrics simplified for beginners")
apply_styles()

DONUT_COLORS = [BLUE, GREEN, ORANGE]  # top 3 stocks; "Others" is gray
DAYS_30 = 21  # about 30 calendar days of trading
CHART_TEXT = "#9CA3AF"  # light gray
NO_TOOLBAR = {"displayModeBar": False}


def style_chart(figure):
    """Dark-friendly chart look: see-through background, no gridlines, light gray text."""
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": CHART_TEXT},
        margin={"t": 10, "b": 10, "l": 10, "r": 10},
        height=260,
    )
    figure.update_xaxes(showgrid=False, zeroline=False)
    figure.update_yaxes(showgrid=False, zeroline=False)
    return figure


def format_or_dash(value, pattern):
    """Format a number, or show "–" if we don't have it."""
    if value is None or pd.isna(value):
        return "–"
    return pattern.format(value)


def beta_note(beta):
    if beta is None:
        return "Not enough price data yet"
    if beta > 1.1:
        return "More volatile than the average market"
    if beta < 0.9:
        return "Steadier than the average market"
    return "Moves about like the market"


def volatility_note(vol):
    if vol is None:
        return "Not enough price data yet"
    if vol < 0.15:
        return "Calm price swings"
    if vol < 0.30:
        return "Standard price swings"
    return "Big price swings"


def sharpe_note(sharpe):
    if sharpe is None:
        return "Not enough price data yet"
    if sharpe >= 1:
        return "Good return relative to risks taken"
    if sharpe >= 0:
        return "Modest return for the risk taken"
    return "Lost money over the past year"


# --- Load the portfolio ---
holdings = {h["ticker"]: h["shares"] for h in get_portfolio() if h["shares"] > 0}
if not holdings:
    st.info("Add stocks (with more than 0 shares) on the **My Stocks** page to see your risk here.")
    st.stop()

with st.spinner("Crunching a year of prices..."):
    sectors = {ticker: get_industry(ticker) for ticker in holdings}
    risk = analyze_portfolio(holdings, sectors)
    prices = get_history_for_many(list(holdings) + [MARKET], "1Y")

weights = risk["weights"]
if not weights:
    st.warning("We couldn't get price history for your stocks right now. Try again in a minute.")
    st.stop()
if risk["missing"]:
    st.warning(f"No price history for: {', '.join(risk['missing'])}. They're left out of the numbers below.")

# --- Extra numbers the risk service doesn't give: per-stock beta and volatility, 30-day volatility, Sharpe ---
returns = daily_returns(prices[[t for t in list(weights) + [MARKET] if t in prices.columns]])
portfolio_daily = sum(returns[t] * w for t, w in weights.items())
yearly = np.sqrt(TRADING_DAYS_PER_YEAR)

recent = portfolio_daily.tail(DAYS_30)
volatility_30d = float(recent.std() * yearly) if len(recent) >= 2 else None

sharpe = None
if len(portfolio_daily) >= 2 and portfolio_daily.std() > 0:
    # Yearly return divided by yearly swings (we treat the "risk-free" rate as 0 to keep it simple)
    sharpe = float(portfolio_daily.mean() * TRADING_DAYS_PER_YEAR / (portfolio_daily.std() * yearly))

stock_volatility = {t: float(returns[t].std() * yearly) for t in weights}
stock_beta = {}
if MARKET in returns.columns and returns[MARKET].var() > 0:
    for t in weights:
        stock_beta[t] = float(returns[t].cov(returns[MARKET]) / returns[MARKET].var())

# --- Four number cards ---
beta = risk["beta"]
drawdown = risk["max_drawdown"]
cols = st.columns(4)
with cols[0]:
    metric_card("Portfolio beta", format_or_dash(beta, "{:.2f}"), beta_note(beta))
with cols[1]:
    metric_card("Volatility (30D)", format_or_dash(volatility_30d, "{:.1%}"), volatility_note(volatility_30d))
with cols[2]:
    metric_card("Max drawdown", format_or_dash(drawdown, "{:.1%}"), "Worst drop from recent high point")
with cols[3]:
    metric_card("Sharpe ratio", format_or_dash(sharpe, "{:.2f}"), sharpe_note(sharpe))

st.write("")

# --- Charts: where the money is, and how much each stock swings ---
left, right = st.columns(2, gap="medium")

with left:
    with card("concentration"):
        st.markdown('<div class="ss-card-title">Portfolio Concentration (Asset Weights)</div>', unsafe_allow_html=True)

        # Sort stocks from biggest to smallest weight
        ranked = []
        for ticker in weights:
            ranked.append((weights[ticker], ticker))
        ranked.sort(reverse=True)

        # Top 3 stocks get their own slice; the rest are added up as "Others"
        labels = []
        values = []
        colors = []
        others = 0.0
        for position in range(len(ranked)):
            weight, ticker = ranked[position]
            if position < 3:
                labels.append(f"{ticker} ({weight:.0%})")
                values.append(weight)
                colors.append(DONUT_COLORS[position])
            else:
                others = others + weight
        if others > 0:
            labels.append(f"Others ({others:.0%})")
            values.append(others)
            colors.append(GRAY)

        donut = go.Figure(go.Pie(
            labels=labels,
            values=values,
            hole=0.6,
            sort=False,
            marker={"colors": colors, "line": {"width": 0}},
            textinfo="none",
            hovertemplate="%{label}<extra></extra>",
        ))
        style_chart(donut)
        donut.update_layout(legend={"orientation": "v", "yanchor": "middle", "y": 0.5})
        st.plotly_chart(donut, width="stretch", config=NO_TOOLBAR, theme=None)

with right:
    with card("volatility"):
        st.markdown('<div class="ss-card-title">Stock Volatility</div>', unsafe_allow_html=True)

        # Sort stocks from calmest to most volatile
        by_volatility = []
        for ticker in stock_volatility:
            by_volatility.append((stock_volatility[ticker], ticker))
        by_volatility.sort()

        bar_names = []
        bar_values = []
        bar_colors = []
        for position in range(len(by_volatility)):
            volatility, ticker = by_volatility[position]
            bar_names.append(ticker)
            bar_values.append(volatility)
            # The last bar is the highest one: make it red
            if position == len(by_volatility) - 1 and len(by_volatility) > 1:
                bar_colors.append(RED)
            else:
                bar_colors.append(BLUE)

        bars = go.Figure(go.Bar(
            x=bar_names,
            y=bar_values,
            marker={"color": bar_colors},
            hovertemplate="%{x}: %{y:.1%} yearly swings<extra></extra>",
        ))
        style_chart(bars)
        bars.update_yaxes(tickformat=".0%")
        st.plotly_chart(bars, width="stretch", config=NO_TOOLBAR, theme=None)

st.write("")

# --- Holdings & Risk Matrix ---
rows_html = ""
for weight, ticker in ranked:
    try:
        quote = get_quote(ticker)
    except StockDataError:
        quote = {"price": None, "percent_change": None}

    # Green for gains, red for losses
    change = quote["percent_change"]
    change_class = ""
    if change is not None and change > 0:
        change_class = "ss-pos"
    elif change is not None and change < 0:
        change_class = "ss-neg"

    rows_html += (
        f"<tr><td><b>{escape(ticker)}</b></td>"
        f'<td class="ss-num">{escape(format_or_dash(quote["price"], "${:,.2f}"))}</td>'
        f'<td class="ss-num {change_class}">{escape(format_or_dash(change, "{:+.2f}%"))}</td>'
        f'<td class="ss-num">{escape(format_or_dash(stock_beta.get(ticker), "{:.2f}"))}</td>'
        f'<td class="ss-num">{escape(format_or_dash(weight, "{:.0%}"))}</td></tr>'
    )

st.markdown(
    '<div class="ss-card"><div class="ss-card-title">Holdings &amp; Risk Matrix</div>'
    '<table class="ss-table"><thead><tr><th>Ticker</th><th class="ss-num">Price</th>'
    '<th class="ss-num">Daily Change</th><th class="ss-num">Beta</th><th class="ss-num">Weight</th></tr></thead>'
    f"<tbody>{rows_html}</tbody></table></div>",
    unsafe_allow_html=True,
)

st.write("")

# --- Plain-English warnings from the risk service ---
if risk["warnings"]:
    st.markdown("#### Things to watch")
    for warning in risk["warnings"]:
        st.markdown(
            f'<div class="ss-alert ss-alert-warn">⚠️ {escape(warning)}</div>',
            unsafe_allow_html=True,
        )
else:
    st.markdown('<div class="ss-alert ss-alert-ok">✓ No major risk flags</div>', unsafe_allow_html=True)

with st.expander("What do these numbers mean?"):
    st.markdown(
        "- **Beta:** how much your portfolio moves when the whole market moves. 1.0 = same as the market.\n"
        "- **Volatility:** how much prices swing, as a yearly percent. Higher means a bumpier ride.\n"
        "- **Max drawdown:** the biggest drop from a high point over the past year.\n"
        "- **Sharpe ratio:** return per unit of risk over the past year. Above 1 is generally good.\n"
        "- **Weight:** how much of your money is in each stock."
    )

st.divider()
st.caption("For learning only, not financial advice.")
