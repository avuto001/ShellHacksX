"""
StockSense data layer (MOCK VERSION).

Every page in the app gets its data from the functions in this file. Right now
they return fake-but-realistic data so the frontend can be built before the
backend is ready.

To connect the real backend: replace the body of each function marked
"TODO: replace with backend call" with a real API call. As long as you return
the same shape (same dictionary keys), the templates and JavaScript keep working
without any changes.

Handy environment variables for testing the UI:
  STOCKSENSE_MOCK_DELAY=1.5   -> wait 1.5 seconds before returning data
                                 (so you can see the loading skeletons)
  STOCKSENSE_MOCK_ERRORS=1    -> make news, summary and chart data fail
                                 (so you can see the error states)
"""

import math
import os
import random
import time as time_module
from datetime import date, datetime, time, timedelta


# The chart timeframes, in the order the toggle buttons appear.
# The value is a friendly label shown next to the chart title.
TIMEFRAMES = {
    "1D": "today",
    "5D": "past 5 days",
    "1M": "past month",
    "YTD": "year to date",
    "1Y": "past year",
}
DEFAULT_TIMEFRAME = "1M"


class DataServiceError(Exception):
    """Raised when data can't be loaded (for example, the backend is down)."""


class UnknownTickerError(DataServiceError):
    """Raised when we don't have any data for the requested ticker."""


# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

# Basic facts about each mock company.
#   price      = current share price in USD
#   volatility = how much the price typically moves in one day (0.01 = 1%)
#   drift      = the stock's general daily trend (positive = trending up)
_COMPANIES = {
    "AAPL": {"name": "Apple Inc.", "sector": "Technology", "price": 227.52, "volatility": 0.014, "drift": 0.0007},
    "NVDA": {"name": "NVIDIA Corporation", "sector": "Semiconductors", "price": 118.85, "volatility": 0.028, "drift": 0.0015},
    "JNJ": {"name": "Johnson & Johnson", "sector": "Healthcare", "price": 162.40, "volatility": 0.009, "drift": 0.0002},
    "KO": {"name": "The Coca-Cola Company", "sector": "Consumer Staples", "price": 69.87, "volatility": 0.008, "drift": 0.0003},
    "TSLA": {"name": "Tesla, Inc.", "sector": "Automotive", "price": 254.22, "volatility": 0.032, "drift": -0.0004},
}

_NEWS = {
    "AAPL": [
        {"headline": "Apple's services revenue hits a record as App Store sales climb", "source": "Reuters", "time_ago": "2h ago", "sentiment": "positive"},
        {"headline": "iPhone demand in China cools ahead of the holiday season", "source": "Bloomberg", "time_ago": "5h ago", "sentiment": "negative"},
        {"headline": "Apple schedules its next product event for late October", "source": "The Verge", "time_ago": "1d ago", "sentiment": "neutral"},
        {"headline": "Analysts raise price targets after strong earnings guidance", "source": "CNBC", "time_ago": "2d ago", "sentiment": "positive"},
    ],
    "NVDA": [
        {"headline": "NVIDIA's data-center sales jump as AI demand keeps growing", "source": "Reuters", "time_ago": "1h ago", "sentiment": "positive"},
        {"headline": "Chip stocks swing as investors question AI spending", "source": "MarketWatch", "time_ago": "4h ago", "sentiment": "negative"},
        {"headline": "NVIDIA unveils next-generation GPU for gaming laptops", "source": "The Verge", "time_ago": "1d ago", "sentiment": "neutral"},
        {"headline": "Supply chain partners expand production to meet orders", "source": "Bloomberg", "time_ago": "3d ago", "sentiment": "positive"},
    ],
    "JNJ": [
        {"headline": "Johnson & Johnson raises its dividend for the 63rd year in a row", "source": "Reuters", "time_ago": "3h ago", "sentiment": "positive"},
        {"headline": "Healthcare stocks steady as investors look for defensive stocks", "source": "CNBC", "time_ago": "6h ago", "sentiment": "neutral"},
        {"headline": "J&J faces new legal challenge over older consumer product", "source": "Bloomberg", "time_ago": "1d ago", "sentiment": "negative"},
        {"headline": "FDA approves J&J treatment for a rare blood disorder", "source": "STAT News", "time_ago": "2d ago", "sentiment": "positive"},
    ],
    "KO": [
        {"headline": "Coca-Cola keeps full-year outlook steady despite higher costs", "source": "Reuters", "time_ago": "2h ago", "sentiment": "neutral"},
        {"headline": "Zero-sugar drinks drive volume growth in Latin America", "source": "Bloomberg", "time_ago": "7h ago", "sentiment": "positive"},
        {"headline": "Strong dollar weighs on international revenue", "source": "The Wall Street Journal", "time_ago": "1d ago", "sentiment": "negative"},
        {"headline": "Consumer staples outperform as markets turn cautious", "source": "MarketWatch", "time_ago": "3d ago", "sentiment": "positive"},
    ],
    "TSLA": [
        {"headline": "Tesla deliveries come in below Wall Street estimates", "source": "Reuters", "time_ago": "1h ago", "sentiment": "negative"},
        {"headline": "Tesla cuts prices on Model Y in several markets", "source": "Bloomberg", "time_ago": "5h ago", "sentiment": "negative"},
        {"headline": "Energy storage business posts its best quarter ever", "source": "CNBC", "time_ago": "1d ago", "sentiment": "positive"},
        {"headline": "Robotaxi pilot expands to two more cities", "source": "The Verge", "time_ago": "2d ago", "sentiment": "neutral"},
    ],
}

_AI_SUMMARIES = {
    "AAPL": {
        "summary_paragraphs": [
            "Apple had a mostly good week. The company reported record revenue from services like the App Store, iCloud and Apple Music, which grow steadily even when fewer people buy new iPhones.",
            "The main worry is slower iPhone sales in China. Analysts still expect solid earnings, and several raised their price targets after Apple gave upbeat guidance for next quarter.",
        ],
        "beginner_insight": "Big companies often have more than one way to make money. When one part of the business slows down (iPhones in China), another part (services) can help balance it out.",
    },
    "NVDA": {
        "summary_paragraphs": [
            "NVIDIA makes the chips that power most AI systems, and demand for them is still very strong. Sales to data centers jumped again this quarter.",
            "Even so, the stock has been volatile. Some investors are asking whether companies will keep spending this much on AI, which leads to big price swings on days with no company news.",
        ],
        "beginner_insight": "A fast-growing company can still have a bumpy stock price. High volatility means bigger ups and downs, so only invest money you won't need in the short term.",
    },
    "JNJ": {
        "summary_paragraphs": [
            "Johnson & Johnson raised its dividend again, continuing a streak of more than 60 years. It also won FDA approval for a new treatment, a positive sign for its drug pipeline.",
            "Healthcare companies like J&J are often called defensive stocks because people need medicine no matter how the economy is doing. A new legal case is worth watching, but it's small compared to the size of the business.",
        ],
        "beginner_insight": "Defensive stocks usually won't double in a year, but they tend to fall less when the overall market drops. Many investors hold some for stability.",
    },
    "KO": {
        "summary_paragraphs": [
            "Coca-Cola kept its yearly outlook the same even though ingredient and shipping costs went up. Zero-sugar drinks are selling well, especially in Latin America.",
            "A strong U.S. dollar lowered the value of sales made in other countries. Coca-Cola is part of the consumer staples sector, which often holds up well when investors feel nervous.",
        ],
        "beginner_insight": "Companies that sell things people buy every day, like drinks and groceries, tend to have steady sales. That's one reason they're popular for long-term investing.",
    },
    "TSLA": {
        "summary_paragraphs": [
            "Tesla delivered fewer cars than Wall Street expected and cut prices on the Model Y to boost demand. Lower prices can help sales but usually squeeze profit margins.",
            "There was good news too: the energy storage business had its best quarter ever. The stock is known for being very volatile, so daily moves of 5% or more aren't unusual.",
        ],
        "beginner_insight": "When a company cuts prices, it may sell more but earn less on each sale. Watch both the number of sales and the profit per sale to get the full picture.",
    },
}

# Jargon words that get a hover definition in the AI summary.
# Keys must be lowercase. Longer phrases win over shorter ones automatically.
_GLOSSARY = {
    "defensive stocks": "Shares in companies that sell things people need in good times and bad (like food, medicine or utilities). They tend to fall less during market downturns.",
    "defensive stock": "A share in a company that sells things people need in good times and bad. It tends to fall less during market downturns.",
    "dividend": "A payment a company makes to its shareholders, usually every quarter, out of its profits.",
    "dividends": "Payments a company makes to its shareholders, usually every quarter, out of its profits.",
    "volatile": "Likely to change price quickly and by a lot, in either direction.",
    "volatility": "How much and how quickly a stock's price moves up and down. High volatility means bigger swings.",
    "earnings": "A company's profit: the money left after paying all its costs. Companies report earnings every quarter.",
    "revenue": "The total money a company brings in from sales, before any costs are subtracted.",
    "guidance": "A company's own forecast of how much it expects to sell or earn in the coming months.",
    "analysts": "Professionals who study companies and publish opinions on whether a stock looks like a good investment.",
    "consumer staples": "Everyday products people keep buying no matter what, like drinks, food, soap and toothpaste.",
    "profit margins": "The share of each sale a company keeps as profit. A 20% margin means $20 profit on every $100 of sales.",
    "fda approval": "Permission from the U.S. Food and Drug Administration to sell a new medicine or medical product.",
}

_BEGINNER_TIPS = [
    "Diversification means spreading money across different stocks to reduce risk.",
    "A stock's price going down for a day doesn't mean the company is in trouble. Look at longer timeframes too.",
    "Investing a fixed amount on a regular schedule is called dollar-cost averaging. It removes the pressure of timing the market.",
    "Index funds hold hundreds of companies at once, which makes them an easy way to diversify.",
    "Only invest money you won't need for at least a few years. Short-term swings are normal.",
    "Fees add up over time. Compare expense ratios before choosing a fund.",
]


# ---------------------------------------------------------------------------
# Public functions (these are what app.py calls)
# ---------------------------------------------------------------------------

def get_watchlist():
    # TODO: replace with backend call
    """Return the list of tickers the user is following."""
    return list(_COMPANIES.keys())


def get_stock_quote(ticker):
    # TODO: replace with backend call
    """
    Return the latest quote for one stock:
    {"ticker", "name", "sector", "price", "change", "change_percent"}
    """
    company = _get_company(ticker)

    # Today's change is measured from the first point of the 1D chart
    # so the header badge always matches the 1D chart color.
    today = _build_history(ticker, "1D")
    open_price = today[0]["price"]
    change = company["price"] - open_price

    return {
        "ticker": ticker.upper(),
        "name": company["name"],
        "sector": company["sector"],
        "price": company["price"],
        "change": round(change, 2),
        "change_percent": round(change / open_price * 100, 2),
    }


def get_price_history(ticker, timeframe):
    # TODO: replace with backend call
    """
    Return price points for the chart, oldest first:
    [{"date": "Sep 4", "price": 221.18}, ...]
    timeframe must be one of TIMEFRAMES ("1D", "5D", "1M", "YTD", "1Y").
    """
    _simulate_network()
    return _build_history(ticker, timeframe)


def get_news(ticker):
    # TODO: replace with backend call
    """
    Return recent headlines, newest first:
    [{"headline", "source", "time_ago", "url", "sentiment"}, ...]
    sentiment is "positive", "neutral" or "negative".
    """
    _get_company(ticker)
    _simulate_network()
    articles = _NEWS.get(ticker.upper(), [])
    return [
        {**article, "url": f"https://example.com/news/{ticker.lower()}/{i}"}
        for i, article in enumerate(articles, start=1)
    ]


def get_ai_summary(ticker):
    # TODO: replace with backend call
    """
    Return a plain-English summary of recent news:
    {"summary_paragraphs": [str, ...], "beginner_insight": str}
    """
    _get_company(ticker)
    _simulate_network()
    return _AI_SUMMARIES[ticker.upper()]


def get_glossary():
    # TODO: replace with backend call (or keep local; it's static content)
    """Return {lowercase term: plain-English definition} for jargon tooltips."""
    return _GLOSSARY


def get_beginner_tips():
    # TODO: replace with backend call (or keep local; it's static content)
    """Return a list of short beginner investing tips for the sidebar."""
    return _BEGINNER_TIPS


# ---------------------------------------------------------------------------
# Helpers for the mock data (delete these once the real backend is connected)
# ---------------------------------------------------------------------------

def _get_company(ticker):
    company = _COMPANIES.get(ticker.upper())
    if company is None:
        raise UnknownTickerError(f"No data for ticker '{ticker}'.")
    return company


def _simulate_network():
    """Pretend to be a slow or broken backend, if the env vars ask for it."""
    delay = float(os.environ.get("STOCKSENSE_MOCK_DELAY", "0"))
    if delay > 0:
        time_module.sleep(delay)
    if os.environ.get("STOCKSENSE_MOCK_ERRORS") == "1":
        raise DataServiceError("Simulated backend error (STOCKSENSE_MOCK_ERRORS=1).")


def _build_history(ticker, timeframe):
    """Generate a believable price series that ends at today's price."""
    if timeframe not in TIMEFRAMES:
        raise ValueError(f"Unknown timeframe '{timeframe}'.")
    company = _get_company(ticker)

    timestamps, steps_per_day = _timestamps_for(timeframe)

    # Seeding with the ticker + timeframe gives the same chart on every
    # reload, instead of a random new one each time.
    rng = random.Random(f"{ticker.upper()}:{timeframe}")
    step_volatility = company["volatility"] / math.sqrt(steps_per_day)
    step_drift = company["drift"] / steps_per_day

    # Walk backwards from today's price so every chart ends at the same number.
    prices = [company["price"]]
    for _ in range(len(timestamps) - 1):
        prices.append(prices[-1] / (1 + rng.gauss(step_drift, step_volatility)))
    prices.reverse()

    return [
        {"date": _format_label(ts, timeframe), "price": round(price, 2)}
        for ts, price in zip(timestamps, prices)
    ]


def _timestamps_for(timeframe):
    """Return (list of datetimes, how many of them fall in one trading day)."""
    last_day = _last_trading_day(date.today())

    if timeframe == "1D":
        # Every 15 minutes from 9:30 AM to 4:00 PM
        market_open = datetime.combine(last_day, time(9, 30))
        return [market_open + timedelta(minutes=15 * i) for i in range(27)], 26

    if timeframe == "5D":
        # Hourly points (9:30 AM to 3:30 PM) for the last 5 trading days
        days = _trading_days_between(last_day - timedelta(days=10), last_day)[-5:]
        stamps = [
            datetime.combine(day, time(9, 30)) + timedelta(hours=h)
            for day in days
            for h in range(7)
        ]
        return stamps, 7

    starts = {
        "1M": last_day - timedelta(days=30),
        "YTD": date(last_day.year, 1, 1),
        "1Y": last_day - timedelta(days=365),
    }
    days = _trading_days_between(starts[timeframe], last_day)
    return [datetime.combine(day, time(16, 0)) for day in days], 1


def _format_label(ts, timeframe):
    clock = ts.strftime("%I:%M %p").lstrip("0")
    if timeframe == "1D":
        return clock                              # "10:30 AM"
    if timeframe == "5D":
        return f"{ts:%a %b} {ts.day}, {clock}"    # "Mon Sep 21, 10:30 AM"
    if timeframe == "1Y":
        return f"{ts:%b} {ts.day}, {ts.year}"     # "Sep 4, 2026"
    return f"{ts:%b} {ts.day}"                    # "Sep 4"


def _last_trading_day(day):
    """Step back to Friday if today is a weekend (holidays are ignored)."""
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def _trading_days_between(start, end):
    days = []
    day = start
    while day <= end:
        if day.weekday() < 5:
            days.append(day)
        day += timedelta(days=1)
    return days
