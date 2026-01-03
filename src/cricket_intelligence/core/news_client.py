"""
News Fetcher Utility

Generic utility for fetching news from GNews API.
Used by both data pipelines and API tools.
"""

import requests


def fetch_news(api_key: str, query: str, max_articles: int = 10, from_date: str = None) -> dict:
    """
    Fetch news from GNews API (generic utility)

    Args:
        api_key: GNews API key
        query: Search query (caller should add topic-specific keywords)
        max_articles: Max articles to fetch (default: 10, GNews free tier max)
        from_date: Optional start date (ISO format)

    Returns:
        Dict with articles_count and articles list
    """
    if not api_key:
        return {"error": "GNews API key not provided"}

    url = "https://gnews.io/api/v4/search"
    params = {
        "q": query,
        "apikey": api_key,
        "lang": "en",
        "max": max_articles
    }

    if from_date:
        params["from"] = from_date

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        articles = []
        if "articles" in data:
            for article in data["articles"]:
                normalized = {
                    "url": article.get("url", ""),
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "content": article.get("content", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "published_at": article.get("publishedAt", "")
                }
                articles.append(normalized)

        return {
            "articles_count": len(articles),
            "articles": articles
        }
    except Exception as e:
        return {"error": f"Failed to fetch from GNews API: {str(e)}"}
