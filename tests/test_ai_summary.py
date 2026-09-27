# Tests for services/ai_summary.py. Run them with: pytest
# These never call the real Claude API: they swap in fake replies instead.

import json

import anthropic
import httpx2

from services import ai_summary
from services.ai_summary import build_prompt, summarize_stock, validate_response

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

    def fake_ask_claude(system_prompt, user_prompt, attempt):
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
