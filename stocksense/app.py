"""
StockSense: a financial literacy dashboard for beginner investors.

This file sets up the Flask app and its routes (URLs). Routes never create data
themselves; they ask services/data_service.py for it and pass it to a template.

Run it with:  flask run   (from inside the stocksense/ folder)
"""

import random
import re

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for
from markupsafe import Markup, escape

from services import data_service

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Layout settings shared by every page
# ---------------------------------------------------------------------------

# Sidebar links. "endpoint" is the name of the route function below.
# Icon names come from https://lucide.dev/icons
NAV_ITEMS = [
    {"endpoint": "my_stocks", "label": "My Stocks", "icon": "briefcase"},
    {"endpoint": "stock_detail", "label": "Stock Detail", "icon": "chart-line"},
    {"endpoint": "daily_summary", "label": "Daily Summary", "icon": "newspaper"},
    {"endpoint": "portfolio_risk", "label": "Portfolio Risk", "icon": "shield-alert"},
    {"endpoint": "ask", "label": "Ask StockSense", "icon": "message-circle"},
]

# Text for the pages that aren't built yet.
COMING_SOON_PAGES = {
    "my_stocks": {
        "title": "My Stocks",
        "icon": "briefcase",
        "description": "Add the stocks you own and see how they're doing at a glance.",
    },
    "daily_summary": {
        "title": "Daily Summary",
        "icon": "newspaper",
        "description": "A short, plain-English recap of what happened to your stocks today.",
    },
    "portfolio_risk": {
        "title": "Portfolio Risk",
        "icon": "shield-alert",
        "description": "See how spread out your money is and which stocks move the most.",
    },
    "ask": {
        "title": "Ask StockSense",
        "icon": "message-circle",
        "description": "Ask questions about investing or your portfolio and get beginner-friendly answers.",
    },
}


@app.context_processor
def inject_layout_data():
    """Variables every template can use (the sidebar needs these)."""
    return {
        "nav_items": NAV_ITEMS,
        # A different tip on each page load
        "beginner_tip": random.choice(data_service.get_beginner_tips()),
    }


# ---------------------------------------------------------------------------
# Template filters
# ---------------------------------------------------------------------------

@app.template_filter("money")
def format_money(value):
    """227.5 -> "227.50", 1234.5 -> "1,234.50" """
    return f"{value:,.2f}"


@app.template_filter("jargon")
def highlight_jargon(text):
    """
    Wrap glossary words (like "defensive stocks") in a span that shows
    a definition tooltip on hover or tap.
    """
    glossary = data_service.get_glossary()
    # Escape the text first so it's safe, then add our own HTML around terms.
    safe_text = str(escape(text))
    terms = sorted(glossary, key=len, reverse=True)  # longest phrases first
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(str(escape(t))) for t in terms) + r")\b",
        re.IGNORECASE,
    )

    def add_tooltip(match):
        word = match.group(0)
        definition = escape(glossary[word.lower()])
        return (
            f'<span class="jargon" tabindex="0">{word}'
            f'<span class="jargon-tip" role="tooltip">{definition}</span></span>'
        )

    return Markup(pattern.sub(add_tooltip, safe_text))


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return redirect(url_for("stock_detail"))


@app.route("/stock/")
@app.route("/stock/<ticker>")
def stock_detail(ticker=None):
    watchlist = data_service.get_watchlist()
    ticker = (ticker or watchlist[0]).upper()

    try:
        quote = data_service.get_stock_quote(ticker)
    except data_service.UnknownTickerError:
        abort(404)

    # The chart, news and summary are loaded by JavaScript after the page
    # appears, so the page shows loading skeletons instead of a blank screen.
    return render_template(
        "stock_detail.html",
        quote=quote,
        watchlist=watchlist,
        timeframes=data_service.TIMEFRAMES,
        default_timeframe=data_service.DEFAULT_TIMEFRAME,
    )


@app.route("/my-stocks")
def my_stocks():
    return render_template("my_stocks.html", page=COMING_SOON_PAGES["my_stocks"])


@app.route("/daily-summary")
def daily_summary():
    return render_template("daily_summary.html", page=COMING_SOON_PAGES["daily_summary"])


@app.route("/portfolio-risk")
def portfolio_risk():
    return render_template("portfolio_risk.html", page=COMING_SOON_PAGES["portfolio_risk"])


@app.route("/ask")
def ask():
    return render_template("ask.html", page=COMING_SOON_PAGES["ask"])


# ---------------------------------------------------------------------------
# Data endpoints (called by JavaScript on the Stock Detail page)
# ---------------------------------------------------------------------------

@app.route("/api/history/<ticker>/<timeframe>")
def api_history(ticker, timeframe):
    """Chart data as JSON, so the chart can switch timeframes without a reload."""
    timeframe = timeframe.upper()
    if timeframe not in data_service.TIMEFRAMES:
        return jsonify(error=f"Unknown timeframe '{timeframe}'."), 400

    try:
        points = data_service.get_price_history(ticker, timeframe)
    except data_service.UnknownTickerError as e:
        return jsonify(error=str(e)), 404
    except data_service.DataServiceError as e:
        return jsonify(error=str(e)), 502

    return jsonify(
        ticker=ticker.upper(),
        timeframe=timeframe,
        period_label=data_service.TIMEFRAMES[timeframe],
        points=points,
    )


@app.route("/partials/news/<ticker>")
def news_partial(ticker):
    """The news list as a ready-made HTML snippet."""
    try:
        news = data_service.get_news(ticker)
    except data_service.UnknownTickerError:
        abort(404)
    except data_service.DataServiceError:
        abort(502)
    return render_template("partials/news_list.html", news=news)


@app.route("/partials/summary/<ticker>")
def summary_partial(ticker):
    """The AI summary as a ready-made HTML snippet."""
    try:
        summary = data_service.get_ai_summary(ticker)
    except data_service.UnknownTickerError:
        abort(404)
    except data_service.DataServiceError:
        abort(502)
    return render_template("partials/ai_summary.html", summary=summary)


@app.errorhandler(404)
def page_not_found(error):
    # Snippet/API requests get a plain 404; full pages get a friendly screen.
    if request.path.startswith(("/api/", "/partials/")):
        return "Not found", 404
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
