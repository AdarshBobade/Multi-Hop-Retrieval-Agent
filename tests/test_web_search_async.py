import asyncio

from app_data import retrieval


def test_web_search_async_keeps_topic_and_search_depth_separate(monkeypatch):
    captured = {}

    def fake_web_search(query, topic="general", search_depth="basic"):
        captured["query"] = query
        captured["topic"] = topic
        captured["search_depth"] = search_depth
        return []

    monkeypatch.setattr(retrieval, "web_search", fake_web_search)

    asyncio.run(retrieval.web_search_async("aerobic and anaerobic respiration", "basic", "general"))

    assert captured == {
        "query": "aerobic and anaerobic respiration",
        "topic": "general",
        "search_depth": "basic",
    }
