# StockSense (Flask frontend)

A financial literacy dashboard for beginner investors, built with Flask, Jinja2,
Tailwind CSS and Chart.js. The data is **mock data** for now, so the frontend
works without the backend.

## Setup

Run these from inside the `stocksense/` folder:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
flask run --debug
```

Then open http://127.0.0.1:5000 in your browser. `--debug` reloads the app
whenever you save a file.

## How it fits together

```
app.py                     Routes: gets data from data_service, renders a template
services/data_service.py   ALL data comes from here (mock for now)
templates/base.html        Sidebar + page layout shared by every page
templates/stock_detail.html
templates/ask.html         Ask StockSense chat page
templates/partials/        Small HTML pieces loaded after the page appears
static/js/app.js           Mobile menu, loading skeletons and error boxes
static/js/chart.js         The price chart
static/js/ask.js           Chat: sending, typing dots, history, copy button
static/css/custom.css      Skeleton shimmer, glowing card, jargon tooltips
```

The Stock Detail page shows the header right away. The chart, news and AI summary
load in the background, with loading skeletons while they wait and a **Retry**
box if they fail. Those requests go to:

| URL | Returns |
| --- | --- |
| `/api/history/<ticker>/<timeframe>` | Chart data as JSON (`1D`, `5D`, `1M`, `YTD`, `1Y`) |
| `/partials/news/<ticker>` | News list HTML |
| `/partials/summary/<ticker>` | AI summary HTML |

The **Ask StockSense** chat sends `POST /api/chat` with `{"message": "..."}` and
gets back `{"paragraphs", "vocab", "related_tickers"}`. For now,
`get_chat_response()` picks a canned answer by keyword (risk, risk score,
Sharpe, diversify, today). The route waits about 1 second on purpose so you can
see the typing dots; remove that `time.sleep` once the real AI is connected.
Chat history is kept in the browser tab's sessionStorage.

## Connecting the real backend

Open `services/data_service.py` and replace the body of each function marked
`# TODO: replace with backend call`. As long as each function returns the same
keys, nothing else needs to change. If the backend fails, raise
`DataServiceError` and the page will show an error box with a Retry button.

## Testing the loading and error states

```bash
STOCKSENSE_MOCK_DELAY=2 flask run     # 2-second delay, so you can see the skeletons
STOCKSENSE_MOCK_ERRORS=1 flask run    # make the chart, news, summary and chat fail
```

## Adding jargon definitions

Add a word and its definition to `_GLOSSARY` in `data_service.py`. It will be
underlined with a hover definition wherever it appears in the AI summary.
