# Tests for services/news_cleaner.py. Run them with: pytest
# They use made-up articles, so no API calls are needed.

from services.news_cleaner import (
    clean_news,
    filter_relevant,
    number_articles,
    remove_duplicates,
    trim_text,
)


def make_article(headline, summary=""):
    """Build a fake article that looks like one from get_news()."""
    return {"headline": headline, "summary": summary, "url": "https://example.com", "source": "Test"}


def test_identical_headlines_only_one_kept():
    news = [
        make_article("Apple releases new iPhone"),
        make_article("Apple releases new iPhone"),
    ]
    result = remove_duplicates(news)
    assert len(result) == 1


def test_nearly_identical_headlines_only_one_kept():
    news = [
        make_article("Apple Releases New iPhone!"),
        make_article("apple releases new iphone"),
        make_article("Apple releases a new iPhone"),
    ]
    result = remove_duplicates(news)
    assert len(result) == 1
    # The first (newest) one is the one kept
    assert result[0]["headline"] == "Apple Releases New iPhone!"


def test_different_headlines_are_all_kept():
    news = [
        make_article("Apple releases new iPhone"),
        make_article("Apple stock falls after earnings miss"),
    ]
    result = remove_duplicates(news)
    assert len(result) == 2


def test_article_about_other_company_removed():
    news = [
        make_article("Apple releases new iPhone"),
        make_article("Tesla recalls 10,000 cars"),
        make_article("Markets rally", summary="Shares of AAPL rose 3%."),
    ]
    result = filter_relevant(news, "AAPL", "Apple Inc")
    headlines = []
    for article in result:
        headlines.append(article["headline"])
    assert headlines == ["Apple releases new iPhone", "Markets rally"]


def test_no_relevant_articles_returns_original_list():
    news = [
        make_article("Tesla recalls 10,000 cars"),
        make_article("Oil prices climb"),
    ]
    result = filter_relevant(news, "AAPL", "Apple Inc")
    assert result == news


def test_long_summary_is_trimmed():
    long_summary = "word " * 100  # 500 characters
    news = [make_article("Apple news", summary=long_summary)]
    result = trim_text(news, max_length=50)
    summary = result[0]["summary"]
    assert summary.endswith("...")
    assert len(summary) <= 53  # 50 characters plus "..."
    # It stopped at a full word, not halfway through one
    assert summary == "word word word word word word word word word word..."


def test_short_summary_is_unchanged():
    news = [make_article("Apple news", summary="Short summary.")]
    result = trim_text(news)
    assert result[0]["summary"] == "Short summary."


def test_articles_are_numbered_with_no_gaps():
    news = [make_article("A"), make_article("B"), make_article("C")]
    result = number_articles(news)
    ids = []
    for article in result:
        ids.append(article["id"])
    assert ids == [1, 2, 3]


def test_clean_news_numbers_after_removing_articles():
    news = [
        make_article("Apple releases new iPhone"),
        make_article("Apple releases new iPhone!"),  # duplicate, removed
        make_article("Tesla recalls 10,000 cars"),  # other company, removed
        make_article("Apple stock falls after earnings"),
        make_article("Why Apple is building its own chips"),
    ]
    result = clean_news(news, "AAPL", "Apple Inc")
    ids = []
    for article in result:
        ids.append(article["id"])
    assert ids == [1, 2, 3]


def test_clean_news_respects_limit():
    topics = [
        "iPhone sales", "chip plans", "earnings", "the App Store", "China demand",
        "a lawsuit", "the Vision headset", "stock buybacks", "a new CEO rumor", "AI features",
    ]
    news = []
    for topic in topics:
        news.append(make_article("Apple news about " + topic))
    result = clean_news(news, "AAPL", "Apple Inc", limit=8)
    assert len(result) == 8


def test_empty_list_returns_empty_list():
    assert clean_news([], "AAPL", "Apple Inc") == []
    assert remove_duplicates([]) == []
    assert filter_relevant([], "AAPL", "Apple Inc") == []
    assert trim_text([]) == []
    assert number_articles([]) == []


def test_missing_fields_do_not_crash():
    news = [{"headline": "Apple news"}, {}]
    result = clean_news(news, "AAPL", None)
    assert result[0]["id"] == 1


def test_original_articles_are_not_changed():
    original = make_article("Apple news", summary="word " * 100)
    clean_news([original], "AAPL", "Apple Inc")
    assert "id" not in original
    assert original["summary"] == "word " * 100
