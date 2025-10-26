"""
Web search module for PRISM using SerpAPI
"""

import os
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

try:
    from serpapi import GoogleSearch  # provided by google-search-results
    SERPAPI_AVAILABLE = True
except Exception:
    SERPAPI_AVAILABLE = False


class WebSearch:
    """Simple wrapper around SerpAPI for Google search"""

    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        if not SERPAPI_AVAILABLE:
            logger.warning("SerpAPI client not available. Install google-search-results.")
        if not self.api_key:
            logger.info("SERPAPI_KEY not set. Web search will be unavailable.")

    def search(self, query: str, num_results: int = 3) -> Dict:
        """
        Perform a web search and return top organic results.
        Returns a dict with 'summary' and 'results' list of {title, link, snippet}.
        """
        if not SERPAPI_AVAILABLE or not self.api_key:
            msg = "Web search unavailable (missing dependency or SERPAPI_KEY)."
            logger.warning(msg)
            return {"summary": msg, "results": []}

        try:
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.api_key,
                "num": num_results,
            }
            search = GoogleSearch(params)
            result = search.get_dict()
            organic = result.get("organic_results", [])[:num_results]
            items: List[Dict] = []
            for r in organic:
                items.append({
                    "title": r.get("title", ""),
                    "link": r.get("link", ""),
                    "snippet": r.get("snippet", r.get("snippet_highlighted_words", "")),
                })
            if items:
                top_titles = ", ".join(i["title"] for i in items[:3] if i.get("title"))
                summary = f"Top results for '{query}': {top_titles}"
            else:
                summary = f"No results found for '{query}'."
            return {"summary": summary, "results": items}
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"summary": "Search error occurred.", "results": []}
