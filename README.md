# StockSense 📈

**Make sense of your stocks.**

StockSense is a web app for our ShellHacks X project. Add the stocks you own and it shows their prices, the latest news and plain-English AI summaries of what's going on. It also has risk charts and a chat where you can ask questions about your portfolio. It's built with Python and [Streamlit](https://streamlit.io), gets stock data from [Finnhub](https://finnhub.io) and uses Claude (from Anthropic) for the AI features.

Who's building what: see [TEAM.md](TEAM.md).

---

## First-time setup

You only do this once. These steps are for a Mac.

### 1. Install the tools

Download and install each of these:

- **VS Code**, the code editor: https://code.visualstudio.com
- **Python**, the programming language (get the latest version): https://www.python.org/downloads/
- **GitHub Desktop**, which syncs code with GitHub without typing commands: https://desktop.github.com
- **Claude Code**, an AI assistant that works inside VS Code: open VS Code, click the Extensions icon in the left sidebar (it looks like four squares), search for **Claude Code** and click **Install**.

### 2. Get the code

1. Open **GitHub Desktop** and sign in with your GitHub account.
2. Click **File → Clone Repository**.
3. Find **ShellHacksX** in the list and click **Clone**.

### 3. Open the project in VS Code

In GitHub Desktop, click **Repository → Open in Visual Studio Code**.

If VS Code asks whether you trust the authors, click **Yes**. If it suggests installing recommended extensions, click **Install**.

### 4. Run the setup script

In VS Code, open a terminal with **Terminal → New Terminal** (from the menu bar at the top of the screen). Then type this and press Enter:

```bash
./setup.sh
```

The script installs everything the app needs. When it's done, it will say **🎉 Setup complete!**

### 5. Add the API keys

1. In VS Code, open the file `.streamlit/secrets.toml`.
2. Paste the keys between the quotes. Ask a teammate for them.
3. Save the file (Cmd+S).

It should look like this, with real keys instead of the placeholders:

```toml
FINNHUB_API_KEY = "your-finnhub-key"
ANTHROPIC_API_KEY = "your-anthropic-key"
```

> 🔒 **Keep the keys secret.** Never paste them into any other file, into GitHub or into a group chat. The `secrets.toml` file is set up so it never gets uploaded to GitHub. In code, always read keys with `st.secrets["..."]`, never by typing the key into a `.py` file.

### 6. Start the app

In the terminal, type:

```bash
./run.sh
```

The app opens in your web browser. If it doesn't, go to **http://localhost:8501**. To stop the app, click in the terminal and press **Ctrl+C**.

---

## Every time you work

1. **Get the latest code.** In GitHub Desktop, click **Fetch origin**, then **Pull origin** if it shows up.
2. **Start the app.** In the VS Code terminal, run `./run.sh`. While the app is running, save a file and the browser page will offer to **Rerun** with your changes.
3. **Save your work to GitHub (commit).** In GitHub Desktop, check the files you changed and type a short summary in the box at the bottom left (like "Add news summary"). Then click **Commit to main**.
4. **Share your work with the team (push).** Click **Push origin** at the top.

💡 Pull often and push often. Try to edit only the files you own (see [TEAM.md](TEAM.md)), so two people don't change the same file at the same time.

---

## Where things go

```
app.py              Starts the app and builds the sidebar
my_stocks.py        Home page: "My Stocks"
pages/              The other pages of the app
services/           Behind-the-scenes code: fetching data, AI, math
utils/              Small helpers shared by every page
tests/              Automatic checks that the code works
eval/               Hand-labeled headlines for measuring AI accuracy
```

**`app.py`** starts the app and builds the sidebar (logo, page links and beginner tip). To add a page to the sidebar, add it to the `PAGES` list there.

**`my_stocks.py`** is the **home page** ("My Stocks") and the first thing you see when the app opens. You add and remove stocks here.

**`pages/`** holds the **other pages.** Each `.py` file becomes a page in the sidebar. The number at the start of the file name sets the order, and the rest becomes the page name. For example, `1_Stock_Detail.py` shows up as "Stock Detail".

| Page | What it does |
|---|---|
| `1_Stock_Detail.py` | One stock: price, news and an AI summary |
| `2_Daily_Summary.py` | "Here's what happened to your stocks today" |
| `3_Portfolio_Risk.py` | Risk numbers and charts |
| `4_Ask_StockSense.py` | Chat to ask questions about your stocks |

**`services/`** holds **behind-the-scenes code** that fetches data or does calculations. Pages call these functions, so the pages themselves stay short and simple.

| File | What it does |
|---|---|
| `stock_data.py` | Gets prices, company names and news from Finnhub (already working) |
| `ai_summary.py` | Sends news to Claude and gets back plain-English summaries |
| `risk.py` | Portfolio math: concentration, volatility, beta, correlation and drawdown |
| `security.py` | Cleans news text before the AI sees it, to protect against "prompt injection" (text that tries to trick the AI) |

**`utils/`** holds **small helpers shared by every page.**

| File | What it does |
|---|---|
| `state.py` | The portfolio list that every page shares. Use `get_portfolio()`, `get_tickers()`, `add_stock()` and `remove_stock()`. |
| `ui.py` | Shared display pieces: `page_header()`, `stock_card()`, `coming_soon()` and the green/red colors |

**`tests/`** holds **automatic checks.** To run them, type `pytest` in the terminal (with the virtual environment on; VS Code's terminal turns it on for you). Green means everything passed.

**`eval/`** holds **headlines we label by hand** (good/bad/neutral), so we can measure how often the AI agrees with us. See [eval/README.md](eval/README.md).

**Other files:**
- `requirements.txt` lists the Python packages the app needs. If you add one, tell the team to run `./setup.sh` again.
- `.streamlit/secrets.toml` holds your API keys. It stays on your computer and is never uploaded.
- `.streamlit/secrets.example.toml` is a blank copy of the secrets file that shows which keys are needed.
- `setup.sh` and `run.sh` are the scripts for setting up and starting the app.

> **Heads up:** the portfolio lives only in your browser tab for now. Refreshing the page starts it over.

### Placeholders

Parts that aren't built yet show a **🚧 Coming soon** box in the app. In the code, look for `# TODO:` comments. Each unfinished function has a description above it (called a docstring) explaining what goes in, what comes out and what to build. Unfinished functions return safe placeholder values (like `0.0` or `""`), so the app never crashes while you work.

---

## Troubleshooting

**"You have not agreed to the Xcode license agreements"**
Run this in the terminal:
```bash
sudo xcodebuild -license
```
Type your Mac password when asked. The letters won't appear as you type, which is normal. Press the spacebar to scroll to the end, then type `agree` and press Enter.

**"permission denied: ./setup.sh" (or ./run.sh)**
Run the script with `bash` in front instead:
```bash
bash setup.sh
bash run.sh
```

**"command not found: python3"**, or a popup asks to install "command line developer tools"
Python isn't installed yet. Install it from https://www.python.org/downloads/, close and reopen the VS Code terminal, then run `./setup.sh` again.

**"No virtual environment found. Run ./setup.sh first."**
Run `./setup.sh`, then try `./run.sh` again.

**"ModuleNotFoundError: No module named ..."**
Someone probably added a new package. Run `./setup.sh` again to install it.

**"command not found: pytest"**
The virtual environment isn't on in this terminal. Run `source .venv/bin/activate`, then `pytest`.

**The app says the API key was rejected, or shows a `KeyError` mentioning `FINNHUB_API_KEY` or `ANTHROPIC_API_KEY`**
Open `.streamlit/secrets.toml` and check that the keys are pasted correctly, inside the quotes, with no extra spaces. Then save the file and restart the app.

**"Port 8501 is already in use"**
The app is already running in another terminal. Find that terminal and press Ctrl+C, or just use the tab that's already open in your browser.

**Still stuck?** Ask Claude Code in VS Code. Paste the error message and ask what's wrong.

testing