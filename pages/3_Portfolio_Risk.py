import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from services.price_history import get_history_for_many
from services.risk import MARKET, TRADING_DAYS_PER_YEAR, analyze_portfolio, daily_returns
from services.stock_data import StockDataError, get_quote
from utils.portfolio import get_industry
from utils.state import get_portfolio
from utils.ui import GREEN, RED, beginner_tip, page_header
from utils.ui import html_text as escape

page_header("Portfolio Risk Health", "Understand volatility and safety metrics simplified for beginners")
beginner_tip()

BLUE = "#3b82f6"
DONUT_COLORS = [BLUE, "#10b981", "#f59e0b", "#8b5cf6", "#6b7280"]  # the last one is "Others"
DAYS_30 = 21  # about 30 calendar days of trading

# Colors come from .streamlit/config.toml, so this page follows the app's theme.
PRIMARY = st.get_option("theme.primaryColor") or BLUE
CARD = st.get_option("theme.secondaryBackgroundColor") or "#f0f2f6"

st.markdown(
    f"""
    <style>
    .ss-kpi {{border: 1px solid {PRIMARY}33; border-radius: 12px; padding: 14px 16px;
             background: {CARD}66; height: 100%;}}
    .ss-kpi-label {{opacity: .7; font-size: .72rem; text-transform: uppercase; letter-spacing: .04em;}}
    .ss-kpi-value {{font-size: 1.7rem; font-weight: 700; margin: 2px 0;}}
    .ss-muted {{opacity: .7; font-size: .8rem;}}
    </style>
    """,
    unsafe_allow_html=True,
)


def kpi(column, label, value, note):
    """Draw one of the four number cards at the top."""
    column.markdown(
        f'<div class="ss-kpi"><div class="ss-kpi-label">{escape(label)}</div>'
        f'<div class="ss-kpi-value">{escape(value)}</div>'
        f'<div class="ss-muted">{escape(note)}</div></div>',
        unsafe_allow_html=True,
    )


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
kpi(cols[0], "Portfolio beta", f"{beta:.2f}" if beta is not None else "–", beta_note(beta))
kpi(cols[1], "Volatility (30D)", f"{volatility_30d:.1%}" if volatility_30d is not None else "–",
    volatility_note(volatility_30d))
kpi(cols[2], "Max drawdown", f"{drawdown:.1%}" if drawdown is not None else "–", "Worst drop from recent high point")
kpi(cols[3], "Sharpe ratio", f"{sharpe:.2f}" if sharpe is not None else "–", sharpe_note(sharpe))

st.write("")

# --- Charts: where the money is, and how much each stock swings ---
left, right = st.columns([1, 1], gap="medium")

with left.container(border=True):
    st.markdown("**Portfolio Concentration (Asset Weights)**")
    ranked = sorted(weights.items(), key=lambda item: item[1], reverse=True)
    slices = ranked[:4] if len(ranked) <= 4 else ranked[:3] + [("Others", sum(w for _, w in ranked[3:]))]
    donut_data = pd.DataFrame(
        {"Stock": [f"{t} ({w:.0%})" for t, w in slices], "Weight": [w for _, w in slices]}
    )
    names = list(donut_data["Stock"])
    has_others = slices[-1][0] == "Others"
    colors = DONUT_COLORS[:3] + [DONUT_COLORS[-1]] if has_others else DONUT_COLORS[: len(names)]
    donut = (
        alt.Chart(donut_data)
        .mark_arc(innerRadius=55, outerRadius=85)
        .encode(
            theta="Weight:Q",
            color=alt.Color("Stock:N", sort=names, scale=alt.Scale(domain=names, range=colors),
                            legend=alt.Legend(title=None, orient="right")),
            tooltip=[alt.Tooltip("Stock:N"), alt.Tooltip("Weight:Q", format=".1%")],
        )
        .properties(height=200)
    )
    st.altair_chart(donut, width="stretch")

with right.container(border=True):
    st.markdown("**Stock Volatility / Volatility Index**")
    riskiest = max(stock_volatility, key=stock_volatility.get)
    bar_data = pd.DataFrame(
        {"Stock": list(stock_volatility), "Volatility": list(stock_volatility.values())}
    ).sort_values("Volatility")
    bars = (
        alt.Chart(bar_data)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=28)
        .encode(
            x=alt.X("Stock:N", sort=list(bar_data["Stock"]), title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Volatility:Q", title=None, axis=alt.Axis(format="%")),
            color=alt.condition(alt.datum.Stock == riskiest, alt.value(RED), alt.value(BLUE)),
            tooltip=[alt.Tooltip("Stock:N"), alt.Tooltip("Volatility:Q", title="Yearly swings", format=".1%")],
        )
        .properties(height=200)
    )
    st.altair_chart(bars, width="stretch")
    if len(stock_volatility) > 1:
        st.caption(f"Red = your biggest swinger ({riskiest}). Based on the past year of daily prices.")

# --- Holdings & Risk Matrix ---
with st.container(border=True):
    st.markdown("**Holdings & Risk Matrix**")
    rows = []
    for ticker, weight in sorted(weights.items(), key=lambda item: item[1], reverse=True):
        try:
            quote = get_quote(ticker)
        except StockDataError:
            quote = {"price": None, "percent_change": None}
        rows.append({
            "Ticker": ticker,
            "Price": quote["price"],
            "Daily Change": quote["percent_change"],
            "Beta": stock_beta.get(ticker),
            "Weight": weight * 100,
        })
    table = pd.DataFrame(rows)

    def color_change(value):
        if pd.isna(value) or value == 0:
            return ""
        return f"color: {GREEN if value > 0 else RED}; font-weight: 600"

    st.dataframe(
        table.style.map(color_change, subset=["Daily Change"]),
        hide_index=True,
        width="stretch",
        column_config={
            "Price": st.column_config.NumberColumn(format="$%.2f"),
            "Daily Change": st.column_config.NumberColumn(format="%+.2f%%"),
            "Beta": st.column_config.NumberColumn(format="%.2f"),
            "Weight": st.column_config.NumberColumn(format="%.0f%%"),
        },
    )

# --- Plain-English warnings from the risk service ---
if risk["warnings"]:
    st.markdown("#### Things to watch")
    for warning in risk["warnings"]:
        st.warning(warning.replace("$", "\\$"), icon=":material/warning:")

with st.expander("What do these numbers mean?"):
    st.markdown(
        "- **Beta:** how much your portfolio moves when the whole market moves. 1.0 = same as the market.\n"
        "- **Volatility:** how much prices swing, as a yearly percent. Higher means a bumpier ride.\n"
        "- **Max drawdown:** the biggest drop from a high point over the past year.\n"
        "- **Sharpe ratio:** return per unit of risk over the past year. Above 1 is generally good.\n"
        "- **Weight:** how much of your money is in each stock."
    )
st.caption("Based on the past year of daily prices. For learning, not financial advice.")
