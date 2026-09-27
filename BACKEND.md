# StockSense Backend

For each file, fill in the functions we agreed on: their inputs and what they return.

## services/stock_data.py
Finnhub: quotes, company profiles, news


## services/price_history.py
yfinance: past prices for charts and risk math


## services/news_cleaner.py
Remove duplicate/off-topic articles, number them for citations


## services/security.py
Clean article text before it goes to the AI (prompt injection protection)


## services/ai_summary.py
Claude: plain-English summary, sentiment, citations


## services/risk.py
Portfolio math: concentration, volatility, beta, correlation, drawdown


## services/private_markets.py
Load and filter the private companies map data


## scripts/build_map_data.py
Download and prepare SEC Form D data (run once)


## data/
Output files from scripts/build_map_data.py


## tests/test_risk.py
Tests for risk.py


## tests/test_news_cleaner.py
Tests for news_cleaner.py


## tests/test_security.py
Tests for security.py


## eval/labeled_headlines.csv
Columns: ticker, headline, human_label


## eval/run_eval.py
Compare AI labels to human labels

