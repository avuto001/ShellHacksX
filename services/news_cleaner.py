# Removes duplicate/off-topic news articles and numbers them for citations.
#
# Every function takes a list of articles (dictionaries from
# services.stock_data.get_news) and returns a NEW list. The original articles
# are never changed.

import re
import string
from difflib import SequenceMatcher

# Headlines this similar (0 = totally different, 1 = identical) count as duplicates
SIMILARITY_THRESHOLD = 0.85

# Endings we strip from company names, so "Apple Inc" also matches "Apple"
COMPANY_ENDINGS = ["inc", "corp", "corporation", "co", "company", "ltd", "llc", "plc", "holdings", "group"]


def _normalize_headline(headline):
    """Lowercase a headline and remove its punctuation, so small differences don't matter."""
    text = headline.lower()

    # Build a new string that skips every punctuation character
    no_punctuation = ""
    for character in text:
        if character not in string.punctuation:
            no_punctuation = no_punctuation + character

    # Turn runs of spaces into single spaces
    words = no_punctuation.split()
    return " ".join(words)


def _short_company_name(company_name):
    """Remove endings like "Inc" or "Corp" from a company name ("Apple Inc" -> "Apple")."""
    words = company_name.split()

    # Keep dropping the last word while it's one of the endings
    while len(words) > 1:
        last_word = words[-1].lower().strip(".,")
        if last_word in COMPANY_ENDINGS:
            words = words[:-1]
        else:
            break

    short_name = " ".join(words)
    return short_name.strip(" ,.")


def _mentions(text, phrase):
    """Return True if `phrase` appears in `text` as a whole word, ignoring capitals.

    Whole words matter: the ticker "F" (Ford) shouldn't match every "f" in the text,
    and "Apple" shouldn't match "Pineapple".
    """
    # \b means "word boundary"; re.escape makes symbols like "." match literally
    pattern = r"\b" + re.escape(phrase) + r"\b"
    match = re.search(pattern, text, re.IGNORECASE)
    return match is not None


def remove_duplicates(news):
    """Remove articles whose headline repeats one we've already kept.

    The news list is newest first, so the first copy we see (the newest) is kept.
    """
    kept_articles = []
    kept_headlines = []  # normalized headlines of the articles we've kept so far

    for article in news:
        headline = _normalize_headline(article.get("headline") or "")

        # Compare this headline with every headline we've already kept
        is_duplicate = False
        for kept_headline in kept_headlines:
            if headline == kept_headline:
                is_duplicate = True
                break
            similarity = SequenceMatcher(None, headline, kept_headline).ratio()
            if similarity > SIMILARITY_THRESHOLD:
                is_duplicate = True
                break

        # Only keep it if it wasn't a duplicate
        if not is_duplicate:
            kept_articles.append(article)
            kept_headlines.append(headline)

    return kept_articles


def filter_relevant(news, ticker, company_name):
    """Keep only articles that mention the ticker or the company in the headline or summary.

    If that would remove every article, the original list is returned instead.
    """
    # Make the list of words to search for: ticker, full name and short name
    search_terms = []
    if ticker:
        search_terms.append(ticker)
    if company_name:
        search_terms.append(company_name)
        short_name = _short_company_name(company_name)
        if short_name and short_name != company_name:
            search_terms.append(short_name)

    relevant_articles = []
    for article in news:
        # Search the headline and summary together
        text = (article.get("headline") or "") + " " + (article.get("summary") or "")

        # Keep the article if any search term appears in it
        for term in search_terms:
            if _mentions(text, term):
                relevant_articles.append(article)
                break

    # Never return an empty list just because of this filter
    if len(relevant_articles) == 0:
        return news
    return relevant_articles


def trim_text(news, max_length=300):
    """Shorten each summary to at most max_length characters, ending at a full word plus "..."."""
    trimmed_articles = []

    for article in news:
        # Copy the article so we don't change the original
        new_article = dict(article)
        summary = article.get("summary") or ""

        if len(summary) > max_length:
            # Cut to the maximum length
            shortened = summary[:max_length]

            # Move back to the last space, so we don't stop in the middle of a word
            last_space = shortened.rfind(" ")
            if last_space > 0:
                shortened = shortened[:last_space]

            # Remove trailing punctuation or spaces, then add "..."
            summary = shortened.rstrip(" ,.;:-") + "..."

        new_article["summary"] = summary
        trimmed_articles.append(new_article)

    return trimmed_articles


def number_articles(news):
    """Give each article an "id" of 1, 2, 3... so the AI can cite them as [1], [2], [3]."""
    numbered_articles = []
    number = 1

    for article in news:
        # Copy the article and add its number
        new_article = dict(article)
        new_article["id"] = number
        numbered_articles.append(new_article)
        number = number + 1

    return numbered_articles


def clean_news(news, ticker, company_name, limit=8):
    """Run every cleaning step in order and return the cleaned, numbered list."""
    # Treat a missing list (None) the same as an empty one
    if not news:
        return []

    # Step 1: remove repeated stories
    articles = remove_duplicates(news)

    # Step 2: drop articles about other companies
    articles = filter_relevant(articles, ticker, company_name)

    # Step 3: shorten long summaries
    articles = trim_text(articles)

    # Step 4: keep only the first `limit` articles (the newest ones)
    articles = articles[:limit]

    # Step 5: number them 1, 2, 3...
    articles = number_articles(articles)

    return articles
