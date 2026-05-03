"""Citation Validator — ensures factual correctness and trustworthiness (PRD §6)."""

from __future__ import annotations

import logging
import re

from schemas.tool_result import SourceCard
from schemas.output import ValidationResult

logger = logging.getLogger(__name__)


class CitationValidator:
    """
    Validates citations in the final output:
    - Verifies [n] references map to real sources
    - Checks that URLs in text belong to known sources
    - Removes lines with hallucinated (unknown) URLs
    - Computes a confidence score based on citation validity
    """

    def validate(self, markdown: str, sources: list[SourceCard]) -> tuple[str, ValidationResult]:
        """
        Returns (cleaned_markdown, validation_result).
        """
        valid_urls = {s.url for s in sources if s.url}
        max_citation_idx = len(sources)

        # Track citation references [n] found in text
        citation_refs = set(map(int, re.findall(r"\[(\d+)\]", markdown)))
        valid_refs = {r for r in citation_refs if 1 <= r <= max_citation_idx}
        invalid_refs = citation_refs - valid_refs

        # Track invalid URLs
        invalid_sources: list[str] = []

        # Filter lines with ungrounded URLs
        lines = markdown.split("\n")
        cleaned_lines: list[str] = []

        for line in lines:
            # Check for URLs in the line
            urls_in_line = re.findall(r"https?://[^\s\)\"'>]+", line)

            if urls_in_line:
                # Keep line only if ALL URLs are from known sources
                unknown_urls = [u for u in urls_in_line if u not in valid_urls]
                if unknown_urls:
                    invalid_sources.extend(unknown_urls)
                    logger.debug("Removing line with unknown URL(s): %s", unknown_urls)
                    continue  # drop the line

            cleaned_lines.append(line)

        # Remove invalid [n] references from text
        cleaned_text = "\n".join(cleaned_lines)
        for ref in invalid_refs:
            cleaned_text = cleaned_text.replace(f"[{ref}]", "")
            logger.debug("Removed invalid citation reference [%d]", ref)

        # Compute confidence score
        total_refs = len(citation_refs)
        valid_count = len(valid_refs)

        if total_refs == 0:
            confidence = 1.0 if not invalid_sources else 0.5
        else:
            confidence = valid_count / total_refs

        # Factor in URL validity
        total_url_mentions = len(invalid_sources) + len(valid_urls)
        if total_url_mentions > 0:
            url_ratio = 1.0 - (len(invalid_sources) / max(total_url_mentions, 1))
            confidence = (confidence + url_ratio) / 2.0

        is_valid = confidence >= 0.7 and len(invalid_sources) == 0

        result = ValidationResult(
            valid=is_valid,
            invalid_sources=invalid_sources,
            confidence_score=round(confidence, 3),
        )
        
        logger.info("   [dim]Confidence score:[/dim] %.3f", result.confidence_score)
        if invalid_sources:
            logger.info("   [dim]Invalid sources:[/dim] %d", len(invalid_sources))
        if invalid_refs:
            logger.info("   [dim]Invalid refs removed:[/dim] %d", len(invalid_refs))

        return cleaned_text, result