from __future__ import annotations
from typing import List
from pydantic import BaseModel

class CritiqueResult(BaseModel):
    issues: List[str]
    improvements: List[str]
    score: float

class ValidationResult(BaseModel):
    valid: bool
    invalid_sources: List[str]
    confidence_score: float
