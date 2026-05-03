# Shadow Writer — Deep Research Agent System

A multi-agent research system that takes a user-defined topic and intent, performs deep web research, and produces high-quality, structured output through iterative refinement.

The system mimics how a human expert works:
1. **Plans** research (Planner Agent)
2. **Gathers** information (Research Agent / Scout)
3. **Writes** a draft (Draft Generator)
4. **Critiques** it (Critic Agent)
5. **Refines** into final output (Synthesizer + Citation Validator)

## Architecture

```text
User Input (topic, purpose, depth, output_format)
   ↓
┌─────────────────┐
│  Planner Agent   │  → subtopics, search queries, research plan
└────────┬────────┘
         ↓
┌─────────────────┐
│  Research Agent  │  → multi-round web research (Tavily + Serper)
│  (Scout)         │     iterates per depth: basic=1, intermediate=3, deep=5
└────────┬────────┘
         ↓
┌─────────────────┐
│ Draft Generator  │  → format-aware first draft (notes/blog/report/tweet/custom)
└────────┬────────┘
         ↓
┌─────────────────┐
│  Critic Agent    │  → issues, improvements, score (0-10)
└────────┬────────┘
         ↓
┌─────────────────┐
│  Synthesizer     │  → refined draft addressing critique
└────────┬────────┘
         ↓
┌──────────────────┐
│ Citation Validator│  → removes hallucinated citations, confidence score
└────────┬─────────┘
         ↓
    Final Output
```

## Layout

```text
shadow_writer/
  main.py              # ResearchApp — high-level OOP API
  research_session.py  # ResearchSession → graph + artifacts
  settings.py          # Env / pydantic-settings
  memory.py            # Optional local SQLite index
  graph/
    shadow_graph.py    # ShadowPipeline — full agent pipeline
  agents/
    scout_agent.py     # Web research agent (Tavily + Serper + scrape)
    brief_writer.py    # Legacy brief writer (still usable)
    tool_context.py    # Per-run source accumulation
    tool_agents/
  reasoning/
    planner_agent.py   # Breaks topic into subtopics + queries
    draft_generator.py # Format-aware draft generation
    critic_agent.py    # Quality evaluation + scoring
    synthesizer_agent.py  # Draft refinement from critique
    citation_validator.py # Grounding + confidence scoring
  tools/
    tavily_search.py
    serper.py
    scrape.py
  models/
    types.py           # ResearchInput, ResearchPlan, CritiqueResult, etc.
    export.py
artifacts/             # gitignored outputs
```

## Virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` → `.env` and add keys (`OPENAI_API_KEY`, plus `TAVILY_API_KEY` / `SERPER_API_KEY`).

## User Input

The system accepts structured input:

```python
{
    "topic": "Agent orchestration frameworks in GenAI",
    "purpose": "learn and create LinkedIn content",
    "depth": "deep",             # basic | intermediate | deep
    "output_format": "blog"      # notes | blog | report | tweet_thread | custom
}
```

| Depth         | Research Rounds |
|---------------|-----------------|
| `basic`       | 1               |
| `intermediate`| 3               |
| `deep`        | 5               |

## Python API

```python
from main import ResearchApp

app = ResearchApp()

# Standard research
result = await app.research(
    topic="Agent orchestration frameworks in GenAI",
    purpose="learn and create LinkedIn content",
    depth="deep",
    output_format="blog",
)

# Deep research (convenience — same as depth="deep")
result = await app.deep_research(
    topic="RAG vs Fine-tuning tradeoffs",
    purpose="write a comparison report",
    output_format="report",
)
```

### Convenience functions

```python
from main import run_research, run_deep_research

md = await run_research("Your topic", depth="intermediate", output_format="notes")
md = await run_deep_research("Your topic", output_format="report")
```

## Output Formats

| Format         | Style |
|----------------|-------|
| `notes`        | Bullet-point summary with headers, scannable |
| `blog`         | Intro → sections → conclusion, conversational |
| `report`       | Executive summary → methodology → findings → recommendations |
| `tweet_thread` | Numbered tweets, hook-first, hashtags |
| `custom`       | User-provided instructions via `custom_instructions` |
