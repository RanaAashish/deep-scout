from __future__ import annotations

import logging
from typing import Any, Dict, List

from agents import Runner

from agent_nodes.scout import create_scout_agent
from agent_nodes.context import (
    reset_source_bucket,
    set_source_bucket,
)
from schemas.output import CritiqueResult, ValidationResult
from schemas.research import ResearchInput, ResearchPlan
from schemas.tool_result import SourceCard
from agents.validator import CitationValidator
from agents.critic import CriticAgent
from agents.drafter import DraftGenerator
from agents.planner import PlannerAgent
from agents.synthesizer import SynthesizerAgent
from core.settings import Settings
from prompts._loader import get_prompt

logger = logging.getLogger(__name__)


# =========================================================
# State Container
# =========================================================

class PipelineState(dict):
    """
    Flexible state container for the pipeline.
    You can later upgrade this to a Pydantic model if needed.
    """
    pass


# =========================================================
# Base Node
# =========================================================

class BaseNode:
    async def run(self, state: PipelineState) -> Dict[str, Any]:
        raise NotImplementedError


# =========================================================
# Scout Node (Research Agent — PRD §5.2)
# =========================================================

class ScoutNode(BaseNode):
    """
    Performs one research round:
    - Calls agent
    - Collects sources
    - Updates transcript
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    async def run(self, state: PipelineState) -> Dict[str, Any]:
        bucket: List[SourceCard] = []
        token = set_source_bucket(bucket)

        try:
            agent = create_scout_agent(self.settings)

            iteration = state.get("iteration", 0)
            max_iter = state.get("max_iterations", 1)
            purpose = state.get("purpose", "")
            subtopics = state.get("subtopics", [])

            # Build subtopic focus for this round
            subtopic_focus = ""
            if subtopics:
                idx = iteration % len(subtopics)
                focus_topics = subtopics[idx: idx + 2]  # cover 1-2 subtopics per round
                subtopic_focus = f"\nFocus on: {', '.join(focus_topics)}"
                logger.info("   [dim]Focus:[/dim]%s", subtopic_focus.replace("\n", " "))

            extra = (state.get("output_instructions") or "").strip()
            extra_block = f"\n\nExtra instructions: {extra}" if extra else ""

            round_template = get_prompt("scout", "round_template")
            prompt = round_template.format(
                round_num=iteration + 1,
                max_iter=max_iter,
                topic=state["topic"],
                purpose=purpose,
                subtopic_focus=subtopic_focus,
                extra_block=extra_block,
                transcript=state.get("scout_transcript") or "(none)",
            )

            result = await Runner.run(agent, prompt)
            final = getattr(result, "final_output", None) or str(result)
            
            logger.info("   [dim]Sources collected this round:[/dim] %d", len(bucket))
            logger.info("   [dim]Round summary length:[/dim] %d chars", len(final))

        finally:
            reset_source_bucket(token)

        merged_sources = self._merge_sources(
            state.get("source_cards") or [],
            bucket,
        )

        return {
            "scout_transcript": (state.get("scout_transcript") or "")
            + "\n\n## Round\n"
            + final,
            "iteration": iteration + 1,
            "source_cards": merged_sources,
        }

    def _merge_sources(
        self,
        existing_dicts: List[Dict],
        batch: List[SourceCard],
    ) -> List[Dict]:
        """
        Merge sources by URL (dedup + better excerpt preference)
        """
        by_url: Dict[str, SourceCard] = {}

        for d in existing_dicts:
            c = SourceCard.model_validate(d)
            if c.url:
                by_url[c.url] = c

        for c in batch:
            if not c.url:
                continue

            if c.url not in by_url:
                by_url[c.url] = c
            elif not by_url[c.url].text_excerpt and c.text_excerpt:
                by_url[c.url] = c

        return [c.model_dump() for c in by_url.values()]


# =========================================================
# Brief Node (legacy — kept for backward compat)
# =========================================================

class BriefNode(BaseNode):
    """
    Generates final research markdown from:
    - Transcript
    - Source cards
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    async def run(self, state: PipelineState) -> Dict[str, Any]:
        from agents_nodes.brief_writer import write_research_brief

        cards = [
            SourceCard.model_validate(d)
            for d in (state.get("source_cards") or [])
        ]

        markdown = await write_research_brief(
            topic=state["topic"],
            scout_transcript=state.get("scout_transcript") or "",
            source_cards=cards,
            settings=self.settings,
        )

        return {"research_markdown": markdown}


# =========================================================
# Full Deep Research Pipeline (PRD §4)
# =========================================================

class ShadowPipeline:
    """
    Multi-agent deep research pipeline:

    Planner → Research (multi-round) → Draft → Critic → Synthesizer → Citation Validator

    Implements the full PRD flow with iterative research and
    single-pass critique-synthesis refinement.
    """

    def __init__(self, settings: Settings, *, use_planner: bool = True):
        self.settings = settings
        self.use_planner = use_planner

        self.scout = ScoutNode(settings)
        self.planner = PlannerAgent(settings)
        self.draft_generator = DraftGenerator(settings)
        self.critic = CriticAgent(settings)
        self.synthesizer = SynthesizerAgent(settings)
        self.validator = CitationValidator()

    async def run(self, state: dict) -> dict:
        # ── Extract research input from state ────────────────
        topic = state["topic"]
        purpose = state.get("purpose", "learn")
        output_format = state.get("output_format", "report")
        custom_instructions = state.get("custom_instructions", "")
        max_iterations = state.get("max_iterations", 3)

        logger.info(
            "[bold cyan]🚀 Starting Shadow Pipeline[/bold cyan]\n"
            "   [blue]Topic:[/blue] %r\n"
            "   [blue]Purpose:[/blue] %r\n"
            "   [blue]Iterations:[/blue] %d\n"
            "   [blue]Format:[/blue] %s",
            topic, purpose, max_iterations, output_format,
        )

        # ── 1. Planner Agent ─────────────────────
        plan = ResearchPlan(
            subtopics=[topic],
            search_queries=[topic],
            research_plan=[f"Research: {topic}"],
        )

        if self.use_planner:
            logger.info("[bold yellow]📋 Running Planner Agent...[/bold yellow]")
            research_input = ResearchInput(
                topic=topic,
                purpose=purpose,
                depth=self._iterations_to_depth(max_iterations),
                output_format=output_format,
                custom_instructions=custom_instructions,
            )
            plan = await self.planner.run(research_input)
            logger.info(
                "[green]✅ Plan Generated:[/green] %d subtopics, %d queries",
                len(plan.subtopics), len(plan.search_queries),
            )

        # Inject plan into state
        state["subtopics"] = plan.subtopics
        state["search_queries"] = plan.search_queries
        state["research_plan"] = plan.research_plan
        state["purpose"] = purpose

        # ── 2. Research Agent — multi-round ──────
        logger.info("[bold yellow]🔍 Starting Research (%d rounds)...[/bold yellow]", max_iterations)

        while state.get("iteration", 0) < max_iterations:
            current_round = state.get("iteration", 0) + 1
            logger.info("[blue]➤ Research round %d/%d[/blue]", current_round, max_iterations)

            update = await self.scout.run(state)
            state.update(update)

        sources = [SourceCard.model_validate(d) for d in state.get("source_cards", [])]
        logger.info("[green]✅ Research complete:[/green] %d sources collected", len(sources))

        # ── 3. Draft Generator ───────────────────
        logger.info("[bold yellow]✍️ Generating %s draft...[/bold yellow]", output_format)

        draft = await self.draft_generator.run(
            topic=topic,
            purpose=purpose,
            output_format=output_format,
            scout_transcript=state.get("scout_transcript", ""),
            source_cards=sources,
            custom_instructions=custom_instructions,
        )

        # ── 4. Critic Agent ──────────────────────
        logger.info("[bold yellow]⚖️ Running Critic Agent...[/bold yellow]")

        critique = await self.critic.run(
            draft, topic=topic, purpose=purpose,
        )
        logger.info(
            "[green]✅ Critique Complete:[/green] score=[bold]%.1f/10[/bold], %d issues, %d improvements",
            critique.score, len(critique.issues), len(critique.improvements),
        )

        state["critique_score"] = critique.score
        state["critique_issues"] = critique.issues
        state["critique_improvements"] = critique.improvements

        # ── 5. Synthesizer Agent (PRD §5.5) ─────────────────
        logger.info("[bold yellow]🧬 Running Synthesizer Agent...[/bold yellow]")

        final_draft = await self.synthesizer.run(
            draft=draft,
            critique=critique,
            topic=topic,
            purpose=purpose,
            output_format=output_format,
            sources=sources,
        )

        # ── 6. Citation Validator (PRD §6) ──────────────────
        logger.info("[bold yellow]🛡️ Running Citation Validator...[/bold yellow]")

        validated_md, validation = self.validator.validate(final_draft, sources)
        logger.info(
            "[green]✅ Validation Complete:[/green] valid=%s, confidence=%.3f, invalid_sources=%d",
            validation.valid, validation.confidence_score, len(validation.invalid_sources),
        )

        state["research_markdown"] = validated_md
        state["validation_result"] = validation.model_dump()

        return state

    @staticmethod
    def _iterations_to_depth(iterations: int) -> str:
        if iterations <= 1:
            return "basic"
        elif iterations <= 3:
            return "intermediate"
        return "deep"


# =========================================================
# LangGraph Adapter
# =========================================================

class LangGraphCompiler:
    """
    Adapter to run pipeline via LangGraph.
    Keeps LangGraph OUT of core logic.
    """

    def __init__(self, pipeline: ShadowPipeline):
        self.pipeline = pipeline

    def compile(self):
        from langgraph.graph import StateGraph, END

        builder = StateGraph(dict)

        builder.add_node("run", self.pipeline.run)
        builder.set_entry_point("run")
        builder.add_edge("run", END)

        return builder.compile()


# =========================================================
# Backward-compatible helper
# =========================================================

def compile_shadow_pipeline(settings: Settings, *, use_planner: bool = True):
    """
    Returns a LangGraph compiled graph for the full deep research pipeline.
    """
    pipeline = ShadowPipeline(settings, use_planner=use_planner)
    return LangGraphCompiler(pipeline).compile()