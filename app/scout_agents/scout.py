from __future__ import annotations

from agents import Agent, function_tool

from scout_agents.context import extend_sources
from schemas.tool_result import SourceCard
from core.providers import get_agent_model
from core.settings import Settings
from tools.scrape import fetch_page_text
from tools.search.serper import serper_search_with_cards
from tools.search.tavily import tavily_search_with_cards
from prompts._loader import get_prompt


def create_scout_agent(settings: Settings) -> Agent:
    """Agent that gathers evidence; tools accumulate into per-run source buckets."""

    @function_tool
    async def search_tavily(query: str) -> str:
        """AI-oriented web search (Tavily). Use tight, specific queries."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("      [bold green]Tavily tool triggered:[/bold green] %s", query)
        text, cards = await tavily_search_with_cards(query, settings)
        logger.info("      [bold green]Tavily search result:[/bold green] %d cards", len(cards))
        extend_sources(cards)
        return text

    @function_tool
    async def search_serp(query: str) -> str:
        """Classic Google SERP snippets (Serper). Good for official pages & news."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("      [bold green]Serper tool triggered:[/bold green] %s", query)
        text, cards = await serper_search_with_cards(query, settings)
        logger.info("      [bold green]Serper search result:[/bold green] %s", cards)
        extend_sources(cards)
        return text

    @function_tool
    async def fetch_page(url: str) -> str:
        """Fetch HTML and return readable text (limited length). Few URLs per round."""
        body = await fetch_page_text(url)
        excerpt = body[:8000] if len(body) <= 8000 else body[:8000] + "\n…(truncated)"
        err = body if body.startswith("Error") else None
        extend_sources(
            [
                SourceCard(
                    url=url,
                    title="",
                    snippet="",
                    text_excerpt=body[:2000],
                    fetch_error=err,
                )
            ]
        )
        return excerpt

    instructions = get_prompt("scout")

    return Agent(
        name="ScoutAgent",
        instructions=instructions,
        tools=[search_tavily, search_serp, fetch_page],
        model=get_agent_model(settings),
    )
