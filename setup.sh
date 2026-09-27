./setup.sh


./run.sh
#!/bin/bash
# One-time setup for StockSense. Run it with: ./setup.sh
# It's safe to run again at any time (for example, after someone adds a new package).

set -e
cd "$(dirname "$0")"

echo "👋 Setting up StockSense..."
echo ""

# 1. Make sure Python is installed
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Python isn't installed. Download it from https://www.python.org/downloads/ and run ./setup.sh again."
    exit 1
fi
echo "✅ Found $(python3 --version)"

# 2. Create the virtual environment (a private folder for this project's packages)
if [ -d ".venv" ]; then
    echo "✅ Virtual environment (.venv) already exists"
else
    echo "📦 Creating virtual environment (.venv)..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
fi

# 3. Turn on the virtual environment
source .venv/bin/activate
echo "✅ Virtual environment activated"

# 4. Install the packages listed in requirements.txt
echo "📥 Installing packages (this can take a minute the first time)..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "✅ Packages installed"

# 5. Create the secrets file for API keys (never overwrites an existing one)
if [ -f ".streamlit/secrets.toml" ]; then
    echo "✅ .streamlit/secrets.toml already exists (left it alone)"
else
    cp .streamlit/secrets.example.toml .streamlit/secrets.toml
    echo "✅ Created .streamlit/secrets.toml"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "👉 Next step: open .streamlit/secrets.toml and paste your API keys between the quotes."
echo "   (Ask a teammate for the keys. Never share them in GitHub or group chats.)"
echo ""
echo "   Then start the app with: ./run.sh"
