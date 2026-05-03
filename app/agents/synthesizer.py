"""Synthesizer Agent — refines draft based on critique feedback (PRD §5.5)."""

from __future__ import annotations

import logging

from schemas.output import CritiqueResult
from schemas.tool_result import SourceCard
from core.providers import get_chat_client
from core.settings import Settings
from prompts._loader import get_prompt

logger = logging.getLogger(__name__)


class SynthesizerAgent:
    """Refines a draft by applying critique feedback."""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def run(
        self,
        *,
        draft: str,
        critique: CritiqueResult,
        topic: str,
        purpose: str,
        output_format: str,
        sources: list[SourceCard],
    ) -> str:
        client = get_chat_client(self.settings)

        # Build source reference
        source_lines = [
            f"[{i}] {c.title or '(untitled)'} — {c.url}"
            for i, c in enumerate(sources, start=1)
        ]

        user_prompt = f"""Topic: {topic}
        Purpose: {purpose}
        Output format: {output_format}

        ## Current Draft:
        {draft}

        ## Critique (score: {critique.score}/10):

        ### Issues found:
        {self._format_list(critique.issues)}

        ### Suggested improvements:
        {self._format_list(critique.improvements)}

        ## Available Sources:
        {chr(10).join(source_lines) if source_lines else "(none)"}

        Please produce an improved version of the draft that addresses all issues
        and improvements while maintaining the {output_format} format.
        """

        logger.info("   [dim]Addressing issues:[/dim] %d", len(critique.issues))
        logger.debug("Synthesizer prompt: %s", user_prompt)

        response = await client.chat.completions.create(
            model=self.settings.openai_writer_model,
            messages=[
                {"role": "system", "content": get_prompt("synthesizer")},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.35,
        )
        
        final = response.choices[0].message.content or draft
        logger.info("   [dim]Final length:[/dim] %d chars", len(final))
        return final

    @staticmethod
    def _format_list(items: list[str]) -> str:
        if not items:
            return "- (none)"
        return "\n".join(f"- {item}" for item in items)
