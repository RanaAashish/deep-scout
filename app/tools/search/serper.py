"""Serper.dev Google SERP backend."""

from __future__ import annotations

import httpx

from schemas.tool_result import SourceCard
from core.settings import Settings

SERPER_URL = "https://google.serper.dev/search"


async def serper_search(query: str, settings: Settings, *, num: int = 8) -> str:
    text, _cards = await serper_search_with_cards(query, settings, num=num)
    return text


async def serper_search_with_cards(
    query: str, settings: Settings, *, num: int = 8
) -> tuple[str, list[SourceCard]]:
    if not settings.serper_api_key:
        logger.warning("      [yellow]Serper: missing SERPER_API_KEY[/yellow]")
        return "Serper: missing SERPER_API_KEY — skipping.", []
    headers = {
        "X-API-KEY": settings.serper_api_key,
        "Content-Type": "application/json",
    }
    payload = {"q": query, "num": num}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(SERPER_URL, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        return f"Serper error: {e!s}", []

    organic = data.get("organic") or []
    if not organic:
        logger.warning("      [red]Serper returned no organic results.[/red] Query: %s, Data: %s", query, data)
    cards: list[SourceCard] = []
    lines: list[str] = ["### Serper (Google) results"]
    for item in organic[:num]:
        title = item.get("title") or ""
        link = item.get("link") or ""
        snippet = (item.get("snippet") or "")[:600]
        cards.append(
            SourceCard(url=link, title=title, snippet=snippet, text_excerpt="")
        )
        lines.append(f"- **{title}**\n  URL: {link}\n  Snippet: {snippet}")
    text = "\n".join(lines) if len(lines) > 1 else "Serper: no results."
    return text, cards
