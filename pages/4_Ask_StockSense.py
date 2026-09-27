import re

import streamlit as st

from services.ai_summary import answer_question
from utils.portfolio import load_portfolio_data
from utils.state import get_portfolio
from utils.ui import beginner_tip, link_citations, page_header
from utils.ui import html_text as escape

page_header("Ask StockSense", "Get friendly summaries and simple finance clarifications instantly")
beginner_tip()

SUGGESTIONS = ["What happened today?", "Should I diversify?", "Explain my risk score"]

# Finance words explained in a "Quick Vocabulary" box when an answer uses them
VOCABULARY = {
    "beta": '"Beta" is a simple scale. Over 1 means volatile; under 1 means steadier, safer, and calmer.',
    "sharpe ratio": '"Sharpe Ratio" shows how much return you get for the risk you take. Higher is better.',
    "p/e ratio": '"P/E ratio" is the price divided by yearly profit per share. Lower can mean cheaper.',
    "diversification": '"Diversification" means spreading money across different stocks to reduce risk.',
    "volatility": '"Volatility" is how much and how fast a price swings up and down.',
    "dividend": 'A "dividend" is cash a company pays its shareholders, usually every few months.',
    "market cap": '"Market cap" is the total value of all a company\'s shares added together.',
    "etf": 'An "ETF" is a basket of many stocks you can buy as one, like a ready-made mix.',
}

# Colors come from .streamlit/config.toml, so this page follows the app's theme.
PRIMARY = st.get_option("theme.primaryColor") or "#3b82f6"
CARD = st.get_option("theme.secondaryBackgroundColor") or "#f0f2f6"

st.markdown(
    f"""
    <style>
    .ss-user {{display: flex; justify-content: flex-end; margin: 6px 0 12px;}}
    .ss-user div {{background: {PRIMARY}; color: #fff; border-radius: 12px 12px 2px 12px;
                  padding: 10px 14px; max-width: 75%; font-size: .9rem;}}
    .ss-vocab {{background: {PRIMARY}14; border-radius: 8px; padding: 10px 12px;
               margin-top: 8px; font-size: .85rem;}}
    </style>
    """,
    unsafe_allow_html=True,
)

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
messages = st.session_state.chat_messages


def vocabulary_for(text):
    """Return the explanation of the first finance word the text uses, or None."""
    for word, meaning in VOCABULARY.items():
        if re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE):
            return meaning
    return None


def show_message(message):
    """Draw one chat message: questions as a bubble on the right, answers on the left."""
    if message["role"] == "user":
        st.markdown(f'<div class="ss-user"><div>{escape(message["content"])}</div></div>', unsafe_allow_html=True)
        return
    with st.chat_message("assistant", avatar=":material/auto_awesome:"):
        with st.container(border=True):
            if not message.get("ok"):
                st.warning(str(message["content"]).replace("$", "\\$"))
                return
            text = link_citations(escape(message["content"]), message.get("articles", []))
            st.markdown(text.replace("\n", "<br>"), unsafe_allow_html=True)
            meaning = vocabulary_for(message["content"])
            if meaning:
                st.markdown(
                    f'<div class="ss-vocab">📖 <b>Quick Vocabulary:</b> {escape(meaning)}</div>',
                    unsafe_allow_html=True,
                )


def ask(question):
    """Send a question to Claude and add both sides to the chat."""
    # Only send Claude the plain text of earlier questions it answered successfully
    history = [{"role": m["role"], "content": m["content"]} for m in messages if m.get("ok")]
    with st.spinner("Looking at your stocks..."):
        stocks, _ = load_portfolio_data()
        result = answer_question(question, stocks, history=history)
    ok = result["available"]
    messages.append({"role": "user", "content": question, "ok": ok})
    messages.append({"role": "assistant", "content": result["answer"], "ok": ok, "articles": result["articles"]})


def pick_suggestion():
    """Queue the clicked suggestion chip as the next question, then unselect the chip."""
    st.session_state.pending_question = st.session_state.suggestion
    st.session_state.suggestion = None


if not get_portfolio():
    st.info("Add stocks on the **My Stocks** page so I can answer questions about them.")

# --- Chat panel ---
chat = st.container(border=True, height=420)

# --- Suggestion chips and the question box ---
st.pills(
    "Suggestions", SUGGESTIONS, key="suggestion", on_change=pick_suggestion, label_visibility="collapsed"
)
with st.form("ask", clear_on_submit=True, border=False):
    col1, col2 = st.columns([6, 1], vertical_alignment="bottom")
    typed = col1.text_input(
        "Question", placeholder='Ask anything about your stocks (e.g. "What is a Sharpe Ratio?") ...',
        label_visibility="collapsed",
    )
    sent = col2.form_submit_button("Send", icon=":material/send:", type="primary", width="stretch")

question = typed.strip() if sent and typed.strip() else st.session_state.pop("pending_question", None)

with chat:
    if question:
        ask(question)
    for message in messages:
        show_message(message)

if messages and st.button("Clear chat", icon=":material/delete:", type="tertiary"):
    messages.clear()
    st.rerun()

st.caption("StockSense is for learning, not financial advice. Don't buy or sell based on its answers alone.")
