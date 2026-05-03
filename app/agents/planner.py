"""Planner Agent — breaks topic into subtopics and search queries (PRD §5.1)."""

from __future__ import annotations

import json
import logging

from schemas.research import ResearchInput, ResearchPlan
from core.providers import get_chat_client
from core.settings import Settings
from prompts._loader import get_prompt

logger = logging.getLogger(__name__)


class PlannerAgent:
    """Creates a structured research plan from user input."""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def run(self, research_input: ResearchInput) -> ResearchPlan:
        client = get_chat_client(self.settings)

        user_prompt = (
            f"Topic: {research_input.topic}\n"
            f"Purpose: {research_input.purpose}\n"
            f"Depth: {research_input.depth}\n"
            f"Output format: {research_input.output_format}"
        )

        try:
            logger.debug("Planner prompt: %s", user_prompt)
            response = await client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": get_prompt("planner")},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            data = json.loads(raw)
            plan = ResearchPlan.model_validate(data)
            
            logger.info("   [dim]Subtopics:[/dim] %s", ", ".join(plan.subtopics))
            logger.info("   [dim]Queries:[/dim] %d total", len(plan.search_queries))
            
            return plan

        except (json.JSONDecodeError, Exception) as exc:
            logger.warning("Planner JSON parse failed (%s), falling back to basic plan", exc)
            # Fallback: use topic as single subtopic
            return ResearchPlan(
                subtopics=[research_input.topic],
                search_queries=[research_input.topic],
                research_plan=[f"Research: {research_input.topic}"],
            )