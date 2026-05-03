from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

class SourceCard(BaseModel):
    url: str
    title: str = ""
    snippet: str = ""
    text_excerpt: Optional[str] = None
    fetch_error: Optional[str] = None
