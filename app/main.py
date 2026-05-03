from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import os
from dotenv import load_dotenv

load_dotenv(override=True)

from core.logging_config import setup_logging
from workflow.session import ResearchSession
from core.settings import get_settings

def _run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{ts}_{uuid.uuid4().hex[:8]}"


class ResearchApp:

    def __init__(
        self,
        max_iterations: Optional[int] = None,
        max_time_minutes: int = 15,
        verbose: bool = False,
        use_planner: bool = True,
    ):
        self.max_iterations = max_iterations
        self.max_time_minutes = max_time_minutes
        self.verbose = verbose
        self.use_planner = use_planner
        
        # Ensure data directory exists
        self.data_dir = Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging with file
        log_file = self.data_dir / "research.log"
        setup_logging(verbose=verbose, log_file=str(log_file))
        
        from workflow.session import ArtifactManager
        self.artifact_manager = ArtifactManager(base_dir=self.data_dir)

    async def research(
        self,
        topic: str,
        purpose: str = "learn",
        depth: str = "intermediate",
        output_format: str = "report",
        custom_instructions: str = "",
        output_instructions: str = "",
        save: bool = True,
    ) -> str:

        if not topic:
            raise ValueError("Topic cannot be empty")

        settings = get_settings()

        session = ResearchSession(
            settings=settings,
            max_iterations=self.max_iterations,
            max_time_minutes=self.max_time_minutes,
            use_planner=self.use_planner,
            artifact_manager=self.artifact_manager,
        )

        rid = _run_id() if save else None

        result = await session.run(
            topic,
            purpose=purpose,
            depth=depth,
            output_format=output_format,
            custom_instructions=custom_instructions,
            output_instructions=output_instructions,
            run_id=rid,
            save=save,
        )

        return result.markdown


async def run_research(
    topic: str,
    purpose: str = "learn",
    depth: str = "intermediate",
    output_format: str = "report",
    **kwargs,
) -> str:
    app = ResearchApp(**kwargs)
    return await app.research(
        topic, purpose=purpose, depth=depth, output_format=output_format,
    )