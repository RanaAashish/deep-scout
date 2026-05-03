from __future__ import annotations
from typing import List
from pydantic import BaseModel

class ResearchPlan(BaseModel):
    subtopics: List[str]
    search_queries: List[str]
    research_plan: List[str]

class ResearchInput(BaseModel):
    topic: str
    purpose: str = "learn"
    depth: str = "intermediate"
    output_format: str = "report"
    custom_instructions: str = ""

DEPTH_MAP = {
    "basic": 1,
    "intermediate": 3,
    "deep": 5,
}
