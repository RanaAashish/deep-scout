"""Critic Agent — evaluates draft quality and identifies improvements (PRD §5.4)."""

from __future__ import annotations

import json
import logging

from schemas.output import CritiqueResult
from core.providers import get_chat_client
from core.settings import Settings
from prompts._loader import get_prompt

logger = logging.getLogger(__name__)


class CriticAgent:
    """Evaluates draft quality and returns structured critique."""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def run(self, draft: str, *, topic: str = "", purpose: str = "") -> CritiqueResult:
        client = get_chat_client(self.settings)

        user_prompt = f"""Topic: {topic}
        Purpose: {purpose}

        ## Draft to evaluate:
        {draft}
        """

        try:
            response = await client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": get_prompt("critic")},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            raw = response.choices[0].message.content or "{}"
            data = json.loads(raw)

            critique = CritiqueResult(
                issues=data.get("issues", []),
                improvements=data.get("improvements", []),
                score=float(data.get("score", 5.0)),
            )
            
            logger.info("   [dim]Score:[/dim] %.1f/10", critique.score)
            logger.info("   [dim]Issues found:[/dim] %d", len(critique.issues))
            
            return critique

        except (json.JSONDecodeError, Exception) as exc:
            logger.warning("Critic JSON parse failed (%s), returning default score", exc)
            return CritiqueResult(
                issues=["Could not parse critique output"],
                improvements=[],
                score=5.0,
            )
