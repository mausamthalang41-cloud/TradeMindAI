from main import format_news_articles


def test_format_news_sorts_newest_first():
    raw = [
        {"headline": "Old news", "source": "A", "url": "a", "datetime": 100},
        {"headline": "New news", "source": "B", "url": "b", "datetime": 300},
        {"headline": "Mid news", "source": "C", "url": "c", "datetime": 200},
    ]
    articles = format_news_articles(raw)
    assert [article["headline"] for article in articles] == [
        "New news",
        "Mid news",
        "Old news",
    ]


def test_format_news_drops_entries_without_a_headline():
    raw = [
        {"headline": "", "source": "A", "url": "a", "datetime": 100},
        {"source": "B", "url": "b", "datetime": 200},
        {"headline": "Real headline", "source": "C", "url": "c", "datetime": 300},
    ]
    articles = format_news_articles(raw)
    assert len(articles) == 1
    assert articles[0]["headline"] == "Real headline"


def test_format_news_respects_limit():
    raw = [
        {"headline": f"Story {i}", "source": "A", "url": "a", "datetime": i}
        for i in range(10)
    ]
    articles = format_news_articles(raw, limit=3)
    assert len(articles) == 3
    assert articles[0]["headline"] == "Story 9"
