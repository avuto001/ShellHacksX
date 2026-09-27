# Tests for services/ai_summary.py. Run them with: pytest
# These never call the real Claude API: they swap in fake replies instead.

import json

import anthropic
import httpx2

from services import ai_summary
from services.ai_summary import (
    answer_question,
    build_portfolio_prompt,
    build_prompt,
    summarize_portfolio_day,
    summarize_stock,
    validate_response,
)

ARTICLES = [
    {"id": 1, "headline": "Apple launches new iPhone", "summary": "Sales start Friday.", "source": "Reuters", "url": "https://example.com/1"},
    {"id": 2, "headline": "Apple faces patent lawsuit", "summary": "A court ruled against Apple.", "source": "CNBC", "url": "https://example.com/2"},
]
QUOTE = {"price": 200.0, "change": -3.5, "percent_change": -1.72}

GOOD_ANSWER = {
    "summary": "Apple released a new iPhone [1]. It also lost a patent case in court [2].",
    "sentiment": "neutral",
    "citations": [1, 2],
    "insight_term": "Lawsuit",
    "insight_text": "A lawsuit is when one side takes another to court to settle a disagreement.",
}


def use_fake_claude(monkeypatch, replies):
    """Make summarize_stock get `replies` (one per attempt) instead of calling Claude."""
    calls = []

    def fake_ask_claude(system_prompt, messages, attempt, max_tokens=None):
        calls.append(attempt)
        reply = replies[len(calls) - 1]
        if isinstance(reply, Exception):
            raise reply
        return reply

    monkeypatch.setattr(ai_summary, "_ask_claude", fake_ask_claude)
    monkeypatch.setattr(ai_summary, "_get_api_key", lambda: "fake-key")
    return calls


# --- build_prompt ---


def test_prompt_numbers_articles_inside_tags():
    prompt = build_prompt("AAPL", "Apple Inc", ARTICLES, QUOTE)
    assert "<articles>" in prompt and "</articles>" in prompt
    assert "[1] Apple launches new iPhone" in prompt
    assert "[2] Apple faces patent lawsuit" in prompt
    assert "-1.72%" in prompt


# --- validate_response ---


def test_good_answer_passes():
    assert validate_response(GOOD_ANSWER, ARTICLES) is True


def test_missing_key_fails():
    answer = dict(GOOD_ANSWER)
    del answer["insight_term"]
    assert validate_response(answer, ARTICLES) is False


def test_bad_sentiment_fails():
    answer = dict(GOOD_ANSWER, sentiment="very good")
    assert validate_response(answer, ARTICLES) is False


def test_citation_to_missing_article_fails():
    answer = dict(GOOD_ANSWER, citations=[1, 7])
    assert validate_response(answer, ARTICLES) is False


def test_made_up_citation_in_summary_text_fails():
    answer = dict(GOOD_ANSWER, summary="Apple released a new iPhone [9].")
    assert validate_response(answer, ARTICLES) is False


def test_advice_fails():
    answer = dict(GOOD_ANSWER, summary="Apple released a new iPhone [1], so you should buy it now.")
    assert validate_response(answer, ARTICLES) is False
    answer = dict(GOOD_ANSWER, summary="Apple is a safe bet after its launch [1].")
    assert validate_response(answer, ARTICLES) is False


def test_not_a_dictionary_fails():
    assert validate_response(None, ARTICLES) is False
    assert validate_response("hello", ARTICLES) is False


# --- summarize_stock ---


def test_no_articles_does_not_call_claude(monkeypatch):
    calls = use_fake_claude(monkeypatch, [])
    result = summarize_stock("AAPL", "Apple Inc", [], QUOTE)
    assert calls == []
    assert result["available"] is False
    assert "Apple Inc" in result["summary"]


def test_good_reply_is_returned(monkeypatch):
    use_fake_claude(monkeypatch, [json.dumps(GOOD_ANSWER)])
    result = summarize_stock("AAPL", "Apple Inc", ARTICLES, QUOTE)
    assert result["available"] is True
    assert result["citations"] == [1, 2]


def test_code_fences_are_removed(monkeypatch):
    use_fake_claude(monkeypatch, ["```json\n" + json.dumps(GOOD_ANSWER) + "\n```"])
    result = summarize_stock("AAPL", "Apple Inc", ARTICLES, QUOTE)
    assert result["available"] is True


def test_retries_once_after_bad_reply(monkeypatch):
    calls = use_fake_claude(monkeypatch, ["this is not JSON", json.dumps(GOOD_ANSWER)])
    result = summarize_stock("AAPL", "Apple Inc", ARTICLES, QUOTE)
    assert calls == [1, 2]
    assert result["available"] is True


def test_two_bad_replies_give_fallback(monkeypatch):
    bad = json.dumps(dict(GOOD_ANSWER, summary="You should buy Apple [1]."))
    calls = use_fake_claude(monkeypatch, [bad, bad])
    result = summarize_stock("AAPL", "Apple Inc", ARTICLES, QUOTE)
    assert calls == [1, 2]
    assert result["available"] is False
    assert "unavailable" in result["summary"]


def test_missing_api_key_gives_fallback(monkeypatch):
    monkeypatch.setattr(ai_summary, "_get_api_key", lambda: None)
    result = summarize_stock("AAPL", "Apple Inc", ARTICLES, QUOTE)
    assert result["available"] is False
    assert "missing" in result["summary"]


def test_api_error_gives_fallback(monkeypatch):
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    use_fake_claude(monkeypatch, [anthropic.APIConnectionError(request=request)])
    result = summarize_stock("AAPL", "Apple Inc", ARTICLES, QUOTE)
    assert result["available"] is False
    assert "connect" in result["summary"]


# --- summarize_portfolio_day ---

PORTFOLIO = [
    {"ticker": "AAPL", "name": "Apple Inc", "shares": 10, "quote": {"price": 200.0, "change": -2.0, "percent_change": -0.99}, "news": ARTICLES},
    {"ticker": "MSFT", "name": "Microsoft Corp", "shares": 5, "quote": {"price": 400.0, "change": 4.0, "percent_change": 1.01},
     "news": [{"id": 1, "headline": "Microsoft cloud sales jump", "summary": "", "source": "Bloomberg", "url": "https://example.com/3"}]},
]


def test_portfolio_articles_are_renumbered_without_repeats():
    result = summarize_portfolio_day([])  # just to make sure the empty case is fine
    assert result["available"] is False
    from services.ai_summary import _number_portfolio_articles
    articles = _number_portfolio_articles(PORTFOLIO)
    ids = []
    tickers = []
    for article in articles:
        ids.append(article["id"])
        tickers.append(article["ticker"])
    assert ids == [1, 2, 3]
    assert tickers == ["AAPL", "AAPL", "MSFT"]
    # The original article still has its old number
    assert PORTFOLIO[1]["news"][0]["id"] == 1


def test_portfolio_prompt_has_the_math_done():
    from services.ai_summary import _number_portfolio_articles
    prompt = build_portfolio_prompt(PORTFOLIO, _number_portfolio_articles(PORTFOLIO))
    # 10 x $200 + 5 x $400 = $4,000 total; -$20 + $20 = $0 change today
    assert "worth $4,000.00" in prompt
    assert "+0.00 dollars" in prompt
    assert "[3] (MSFT) Microsoft cloud sales jump" in prompt


def test_portfolio_recap_is_returned(monkeypatch):
    reply = json.dumps({"summary": "Your portfolio was flat today. Microsoft rose after strong cloud sales [3].", "citations": [3]})
    use_fake_claude(monkeypatch, [reply])
    result = summarize_portfolio_day(PORTFOLIO)
    assert result["available"] is True
    assert result["citations"] == [3]
    assert len(result["articles"]) == 3


def test_portfolio_recap_with_fake_citation_gives_fallback(monkeypatch):
    bad = json.dumps({"summary": "Microsoft rose [8].", "citations": [8]})
    use_fake_claude(monkeypatch, [bad, bad])
    result = summarize_portfolio_day(PORTFOLIO)
    assert result["available"] is False


# --- answer_question ---


def test_answer_is_returned(monkeypatch):
    reply = json.dumps({"answer": "Apple fell a little today, maybe because of a court case [2].", "citations": [2]})
    use_fake_claude(monkeypatch, [reply])
    result = answer_question("Why did Apple drop?", PORTFOLIO)
    assert result["available"] is True
    assert result["citations"] == [2]


def test_general_answer_needs_no_citations(monkeypatch):
    reply = json.dumps({"answer": "A dividend is a small payment a company gives to its shareholders.", "citations": []})
    use_fake_claude(monkeypatch, [reply])
    result = answer_question("What is a dividend?", PORTFOLIO)
    assert result["available"] is True


def test_advice_answer_gives_fallback(monkeypatch):
    bad = json.dumps({"answer": "Apple is a safe bet right now.", "citations": []})
    use_fake_claude(monkeypatch, [bad, bad])
    result = answer_question("Should I buy Apple?", PORTFOLIO)
    assert result["available"] is False


def test_history_is_sent_before_the_new_question(monkeypatch):
    sent = []

    def fake_ask_claude(system_prompt, messages, attempt, max_tokens=None):
        sent.append(messages)
        return json.dumps({"answer": "Sure.", "citations": []})

    monkeypatch.setattr(ai_summary, "_ask_claude", fake_ask_claude)
    monkeypatch.setattr(ai_summary, "_get_api_key", lambda: "fake-key")
    history = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}]
    answer_question("Why did Apple drop?", PORTFOLIO, history)
    messages = sent[0]
    assert messages[0] == {"role": "user", "content": "Hi"}
    assert messages[1] == {"role": "assistant", "content": "Hello!"}
    assert messages[2]["content"].endswith("Question: Why did Apple drop?")


def test_empty_question_does_not_call_claude(monkeypatch):
    calls = use_fake_claude(monkeypatch, [])
    result = answer_question("   ", PORTFOLIO)
    assert calls == []
    assert result["available"] is False
