#!/bin/bash
# Starts StockSense. Run it with: ./run.sh
# Stop the app with Ctrl+C.

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "❌ No virtual environment found. Run ./setup.sh first."
    exit 1
fi

source .venv/bin/activate
echo "🚀 Starting StockSense... (press Ctrl+C to stop)"
streamlit run app.py
