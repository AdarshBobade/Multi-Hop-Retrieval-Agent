from app_data.config import tavily_api
from app_data.models import Question
from tavily import TavilyClient

client = TavilyClient(api_key=tavily_api)

def web_search(query:Question,
               topic: str = "general",
               search_depth: str = "basic"):
    
    web_response = client.search(
                                query=query,
                                search_depth=search_depth,
                                topic=topic,
                                max_results=5,
                                include_answer=False,
                                include_raw_content=(search_depth == "advanced")
                            )

    results = []

    for result in web_response.get("results", []):
        if result.get("score", 0) < 0.4:
            continue

        results.append({
            "title": result.get("title"),
            "url": result.get("url"),
            "content": result.get("content"),
            "score": result.get("score", 0.0)
        })