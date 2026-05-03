"""Tavily search backend."""

from __future__ import annotations
import logging

from tavily import AsyncTavilyClient

from schemas.tool_result import SourceCard
from core.settings import Settings


async def tavily_search(query: str, settings: Settings, *, max_results: int = 5) -> str:
    text, _cards = await tavily_search_with_cards(query, settings, max_results=max_results)
    return text


async def tavily_search_with_cards(
    query: str, settings: Settings, *, max_results: int = 5
) -> tuple[str, list[SourceCard]]:
    if not settings.tavily_api_key:
        return "Tavily: missing TAVILY_API_KEY — skipping.", []
    client = AsyncTavilyClient(api_key=settings.tavily_api_key)
    logger = logging.getLogger(__name__)
    logger.info("      [dim]Tavily search:[/dim] %s", query)
    try:
        resp = await client.search(query, max_results=max_results)
    except Exception as e:
        logger.warning("      [red]Tavily error:[/red] %s", e)
        return f"Tavily error: {e!s}", []
    results = resp.get("results") or []
    logger.info("      [dim]Found %d results[/dim]", len(results))
    cards: list[SourceCard] = []
    lines: list[str] = ["### Tavily results"]
    for r in results:
        title = r.get("title") or ""
        url = r.get("url") or ""
        content = (r.get("content") or "")[:800]
        cards.append(
            SourceCard(url=url, title=title, snippet=content, text_excerpt="")
        )
        lines.append(f"- **{title}**\n  URL: {url}\n  Snippet: {content}")
    text = "\n".join(lines) if len(lines) > 1 else "Tavily: no results."
    return text, cards
