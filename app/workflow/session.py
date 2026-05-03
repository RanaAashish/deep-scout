from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Optional

from workflow.graph import compile_shadow_pipeline
from agents.scout import create_scout_agent
from schemas.export import sources_to_json
from schemas.research import DEPTH_MAP, ResearchInput
from schemas.tool_result import SourceCard
from schemas.output import ValidationResult
from core.providers import _resolve_api_key
from core.settings import Settings

logger = logging.getLogger(__name__)


class ResearchResult:
    """Structured result object (better than returning raw string)."""

    def __init__(
        self,
        markdown: str,
        sources: list[SourceCard],
        elapsed: float,
        validation: Optional[ValidationResult] = None,
        critique_score: Optional[float] = None,
        intermediate_data: Optional[str] = None,
    ):
        self.markdown = markdown
        self.sources = sources
        self.elapsed = elapsed
        self.validation = validation
        self.critique_score = critique_score
        self.intermediate_data = intermediate_data


class ArtifactManager:
    """Handles persistence (separated from execution)."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)

    def save(self, run_id: str, result: ResearchResult, query: str) -> Path:
        out_dir = self.base_dir / run_id
        out_dir.mkdir(parents=True, exist_ok=True)

        (out_dir / "research.md").write_text(result.markdown, encoding="utf-8")
        (out_dir / "sources.json").write_text(
            sources_to_json(result.sources, query),
            encoding="utf-8",
        )
        if result.intermediate_data:
            (out_dir / "transcript.txt").write_text(
                result.intermediate_data,
                encoding="utf-8",
            )

        return out_dir


class ResearchSession:
    def __init__(
        self,
        *,
        settings: Settings,
        max_iterations: Optional[int] = None,
        max_time_minutes: int = 15,
        artifact_manager: Optional[ArtifactManager] = None,
        use_planner: bool = True,
    ) -> None:
        # Validate that the configured provider has an API key
        _resolve_api_key(settings)

        self.settings = settings
        self.max_iterations = max_iterations
        self.max_time_minutes = max_time_minutes
        self.artifact_manager = artifact_manager
        self.use_planner = use_planner

        # Compile once (important optimization)
        self.graph = compile_shadow_pipeline(settings, use_planner=use_planner)

    async def run(
        self,
        query: str,
        *,
        purpose: str = "learn",
        depth: str = "intermediate",
        output_format: str = "report",
        custom_instructions: str = "",
        output_length: str = "",
        output_instructions: str = "",
        run_id: Optional[str] = None,
        save: bool = False,
    ) -> ResearchResult:
        if not query:
            raise ValueError("Query cannot be empty")

        start = time.monotonic()

        # Determine max iterations: explicit > depth-based
        max_iter = self.max_iterations or DEPTH_MAP.get(depth, 3)

        instructions = output_instructions or ""
        if output_length:
            instructions = f"Target length/style: {output_length}\n{instructions}".strip()

        initial: dict[str, Any] = {
            "topic": query,
            "purpose": purpose,
            "output_format": output_format,
            "custom_instructions": custom_instructions,
            "max_iterations": max_iter,
            "iteration": 0,
            "scout_transcript": "",
            "source_cards": [],
            "output_instructions": instructions,
        }

        timeout_sec = max(1.0, float(self.max_time_minutes) * 60.0)

        try:
            final_state = await asyncio.wait_for(
                self.graph.ainvoke(initial),
                timeout=timeout_sec,
            )
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Research exceeded {self.max_time_minutes} minutes."
            ) from None

        elapsed = time.monotonic() - start

        # Extract result
        md = final_state.get("research_markdown") or ""
        cards_raw = final_state.get("source_cards") or []
        cards = [SourceCard.model_validate(d) for d in cards_raw]

        # Extract validation & critique metadata
        validation = None
        validation_raw = final_state.get("validation_result")
        if validation_raw:
            validation = ValidationResult.model_validate(validation_raw)

        critique_score = final_state.get("critique_score")

        result = ResearchResult(
            markdown=md,
            sources=cards,
            elapsed=elapsed,
            validation=validation,
            critique_score=critique_score,
            intermediate_data=final_state.get("scout_transcript"),
        )

        # Optional persistence (clean separation)
        if save and run_id and self.artifact_manager:
            self.artifact_manager.save(run_id, result, query)

        return result