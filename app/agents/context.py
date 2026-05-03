"""Per-run accumulation of SourceCards for Agents SDK tool calls."""

from __future__ import annotations

from contextvars import ContextVar

from schemas.tool_result import SourceCard

_source_accumulator: ContextVar[list[SourceCard] | None] = ContextVar(
    "source_accumulator", default=None
)


def set_source_bucket(bucket: list[SourceCard]) -> object:
    return _source_accumulator.set(bucket)


def reset_source_bucket(token: object) -> None:
    _source_accumulator.reset(token)


def extend_sources(cards: list[SourceCard]) -> None:
    import logging
    logger = logging.getLogger(__name__)
    bucket = _source_accumulator.get()
    if bucket is not None:
        logger.debug("   [dim]Extending sources:[/dim] adding %d cards", len(cards))
        bucket.extend(cards)
    else:
        logger.warning("   [red]Context Error:[/red] No source bucket found in current context!")
