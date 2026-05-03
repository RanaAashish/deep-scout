"""Serialize artifacts for disk — keeps agents free of JSON wiring."""

from __future__ import annotations

import json

from schemas.tool_result import SourceCard


def sources_to_json(source_cards: list[SourceCard], topic: str) -> str:
    payload = {"topic": topic, "source_cards": [c.model_dump() for c in source_cards]}
    return json.dumps(payload, indent=2)
