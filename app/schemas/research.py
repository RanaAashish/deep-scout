from pydantic import BaseModel
from typing import List

class ResearchInput(BaseModel):
    topic: str
    purpose: str = "learn"
    depth: str = "standard"  # brief, standard, comprehensive
    output_format: str = "explain"  # tutorial, deep-dive, comparison, explain, custom
    custom_instructions: str = ""
    target_audience: str = "technical"
    tone: str = "professional"  # formal, conversational, technical


class ResearchPlan(BaseModel):
    subtopics: List[str] = []
    search_queries: List[str] = []
    research_plan: List[str] = []


DEPTH_MAP = {
    "brief": 2,
    "standard": 3,
    "comprehensive": 5,
}