from __future__ import annotations

from pydantic import BaseModel
from typing import List


class ArticleMetadata(BaseModel):
    structure_type: str  # tutorial, deep-dive, comparison, explain, custom
    target_audience: str  # beginner, intermediate, advanced
    estimated_read_time: str  # e.g., "5 min read"
    tone: str  # formal, conversational, technical
    word_count: int
    citation_count: int

class Section(BaseModel):
    title: str
    level: int  # 1, 2, 3
    content: str
    subsections: List[Section] = []

class FormattedOutput(BaseModel):
    markdown: str
    metadata: ArticleMetadata
    sections: List[Section]


class CritiqueResult(BaseModel):
    issues: List[str] = []
    improvements: List[str] = []
    score: float = 5.0


class ValidationResult(BaseModel):
    valid: bool = False
    invalid_sources: List[str] = []
    confidence_score: float = 0.0
