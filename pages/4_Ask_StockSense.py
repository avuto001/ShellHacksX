import streamlit as st

from services.ai_summary import answer_question
from services.stock_data import StockDataError, get_company_name, get_news, get_quote
from utils.state import get_portfolio
from utils.ui import beginner_tip, coming_soon, page_header

page_header("Ask StockSense", "Ask questions about your stocks in plain English.")
beginner_tip()

coming_soon(
    "A chat box where you can ask things like \"Why did Apple drop today?\" or "
    "\"Which of my stocks is riskiest?\" Claude will answer using your portfolio, "
    "prices and recent news."
)

SUGGESTIONS = {
    ":material/trending_down: Why did Apple drop today?": "Why did Apple drop today?",
    ":material/warning: Which of my stocks is riskiest?": "Which of my stocks is riskiest?",
    ":material/newspaper: What's the biggest news for my stocks?": "What's the biggest news for my stocks this week?",
}
NOT_READY = (
    "I can't answer yet: the AI part of Ask StockSense is still being built. "
    "Once it's ready, I'll answer using your portfolio, prices and recent news."
)

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
messages = st.session_state.chat_messages


def show(text):
    """Show chat text; "\\$" stops Streamlit from reading two dollar signs as a math formula."""
    st.markdown(text.replace("$", "\\$"))


def portfolio_data():
    """Collect price and news for every stock, in the format answer_question() expects."""
    data = []
    for holding in get_portfolio():
        ticker = holding["ticker"]
        try:
            data.append({
                "ticker": ticker,
                "name": get_company_name(ticker),
                "shares": holding["shares"],
                "quote": get_quote(ticker),
                "news": get_news(ticker),
            })
        except StockDataError:
            continue  # skip stocks Finnhub can't load right now
    return data


if not get_portfolio():
    st.info("Add stocks on the **My Stocks** page so I can answer questions about them.")

# --- Chat history ---
for message in messages:
    with st.chat_message(message["role"]):
        show(message["content"])

# --- New question, typed or picked from the suggestions ---
prompt = st.chat_input("Ask about your stocks...", submit_mode="disable")
if not messages:
    picked = st.pills("Try asking", list(SUGGESTIONS), label_visibility="collapsed", key="suggestion")
    if picked and not prompt:
        prompt = SUGGESTIONS[picked]

if prompt:
    with st.chat_message("user"):
        show(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Looking at your stocks..."):
            answer = answer_question(prompt, portfolio_data(), history=list(messages)) or NOT_READY
        show(answer)

    messages.append({"role": "user", "content": prompt})
    messages.append({"role": "assistant", "content": answer})

if messages and st.button("Clear chat", icon=":material/delete:", type="tertiary"):
    messages.clear()
    st.session_state.pop("suggestion", None)  # so the old suggestion isn't asked again
    st.rerun()

st.caption("StockSense is for learning, not financial advice. Don't buy or sell based on its answers alone.")
