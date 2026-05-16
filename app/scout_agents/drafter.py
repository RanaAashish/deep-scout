"""Draft Generator — converts research findings into a format-aware first draft (PRD §5.3)."""

from __future__ import annotations

import logging

from schemas.tool_result import SourceCard
from core.providers import get_chat_client
from core.settings import Settings
from prompts._loader import get_prompt

logger = logging.getLogger(__name__)


class DraftGenerator:
    """Converts research transcript + sources into a format-specific first draft."""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def run(
        self,
        *,
        topic: str,
        purpose: str,
        output_format: str,
        scout_transcript: str,
        sources: list[SourceCard],
        custom_instructions: str = "",
    ) -> str:
        client = get_chat_client(self.settings)

        # Build numbered source list
        numbered_sources = self._format_sources(sources)

        # Select format prompt
        format_prompt = get_prompt("drafter", "formats", output_format)
        if not format_prompt:
            logger.info(
                "   [dim]Draft format %r not found; using custom flexible format[/dim]",
                output_format,
            )
            format_prompt = get_prompt("drafter", "formats", "custom")
            output_format = "custom"

        system_base = get_prompt("drafter", "base")
        system = system_base.format(format_prompt=format_prompt, purpose=purpose)

        if custom_instructions:
            system += f"\n\nCustom instructions from user:\n{custom_instructions}"

        user_content = f"""Topic: {topic}
        Purpose: {purpose}

        ## Research Notes (tool-grounded transcript)
        {scout_transcript}

        ## Numbered Sources (use [n] citations)
        {numbered_sources}
        """

        logger.info("   [dim]Sources provided:[/dim] %d", len(sources))
        logger.debug("System prompt: %s", system)

        response = await client.chat.completions.create(
            model=self.settings.openai_writer_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            temperature=0.4,
        )
        
        draft = response.choices[0].message.content or ""
        logger.info("   [dim]Draft length:[/dim] %d chars", len(draft))
        return draft

    @staticmethod
    def _format_sources(sources: list[SourceCard]) -> str:
        if not sources:
            return "(no structured sources — stay conservative)"

        lines: list[str] = []
        for i, c in enumerate(sources, start=1):
            line = f"[{i}] {c.title or '(untitled)'} — {c.url}\n   Snippet: {c.snippet[:400]}"
            if c.text_excerpt:
                line += f"\n   Excerpt: {c.text_excerpt[:600]}"
            if c.fetch_error:
                line += f"\n   Note: {c.fetch_error}"
            lines.append(line)
        return "\n".join(lines)
