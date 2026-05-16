# 🔭 Deep Scout

### A powerful, modular, multi-agent AI research system

*Autonomously explores topics · Gathers information from the web · Produces high-quality research outputs*

---

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-2ea043?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-3fb950?style=flat-square)
![Agents](https://img.shields.io/badge/Agents-6_Specialized-bc8cff?style=flat-square)

---

## 🏗️ Architecture

The research pipeline runs sequentially through **6 specialized agents**:

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────────┐   ┌───────────┐
│ Planner  │──▶│  Scout   │──▶│ Drafter  │──▶│  Critic  │──▶│ Synthesizer│──▶│ Validator │
│    📋    │   │(N rounds)│   │    ✍️    │   │    ⚖️    │   │     🧬     │   │    🛡️    │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └────────────┘   └───────────┘
     │               │               │               │               │               │
     ▼               ▼               ▼               ▼               ▼               ▼
   Plan           Sources          Draft          Critique         Final          Validated
                                                  + Score          Output         Citations
```

| # | Agent | Role |
|---|-------|------|
| 1 | 📋 **Planner** | Analyzes topic, creates research plan with subtopics and search queries |
| 2 | 🔍 **Scout** | Executes research using Tavily, gathers sources *(N rounds)* |
| 3 | ✍️ **Drafter** | Generates initial content from research transcript and sources |
| 4 | ⚖️ **Critic** | Evaluates draft quality, assigns score, identifies issues and improvements |
| 5 | 🧬 **Synthesizer** | Refines and polishes content incorporating critic feedback |
| 6 | 🛡️ **Validator** | Validates all citations, ensures source credibility |

---

## 🚀 Quick Start

### 1 · Clone & Install

```bash
git clone https://github.com/RanaAashish/deep-scout.git
cd deep-scout
pip install -r requirements.txt
```

### 2 · Configure Environment

Create a `.env` file in the project root:

```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_key
TAVILY_API_KEY=your_tavily_key
SERPER_API_KEY=your_serper_key
OPENAI_MODEL=openai/gpt-4o-mini
```

### 3 · Run the App

```bash
streamlit run app/streamlit_app.py
```

---

## 🖥️ Streamlit Interface

### Input Panel

Enter your research topic and configure settings:

| Setting | Options |
|---------|---------|
| **Topic** | What you want to research |
| **Purpose** | `learn` · `write` · `compare` · `debug` |
| **Depth** | `basic` (2 rounds) · `intermediate` (3 rounds) · `deep` (5 rounds) |
| **Output Format** | `report` · `tutorial` · `deep-dive` · `comparison` · `explain` |

### Research Progress

Watch the research pipeline execute in real-time:

```
📋  Research plan generated
🔍  Each research round with source count
✍️  Draft generated
⚖️  Critique complete with score
🧬  Synthesis in progress
🛡️  Citation validation
```

### Final Output

The results display:
- ✅ Complete markdown article
- 📊 Source count and critique score
- 🎯 Confidence score

---

## 📖 Usage Guide

### Output Formats

| Format | Use Case |
|--------|----------|
| `report` | General research |
| `tutorial` | Learning a topic |
| `deep-dive` | Technical exploration |
| `comparison` | Comparing options |
| `explain` | Concept explanation |

### Purpose Modes

| Purpose | Description |
|---------|-------------|
| `learn` | Educational content with clear explanations |
| `write` | Publication-ready content |
| `compare` | Side-by-side comparisons |
| `debug` | Problem analysis and solutions |

### Depth Levels

| Depth | Iterations | Use Case |
|-------|------------|----------|
| `basic` | 2 | Quick overview |
| `intermediate` | 3 | Standard research |
| `deep` | 5 | Comprehensive analysis |

---

## ⚙️ Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (`openrouter` \| `openai`) | `openrouter` |
| `OPENROUTER_API_KEY` | OpenRouter API key | — |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `TAVILY_API_KEY` | Tavily search API key | — |
| `SERPER_API_KEY` | Serper search API key | — |
| `OPENAI_MODEL` | Model for research agents | `openai/gpt-4o-mini` |
| `OPENAI_WRITER_MODEL` | Model for writing agents | `openai/gpt-4o-mini` |

---

## 📁 Project Structure

```
deep-scout/
├── app/
│   ├── streamlit_app.py          # Streamlit web interface
│   ├── core/                     # Core utilities
│   │   ├── settings.py           # Configuration
│   │   ├── providers.py          # LLM providers
│   │   └── logging_config.py     # Logging setup
│   ├── scout_agents/             # Agent implementations
│   │   ├── planner.py            # Planning agent
│   │   ├── scout.py              # Research agent
│   │   ├── drafter.py            # Draft generation
│   │   ├── critic.py             # Quality critique
│   │   ├── synthesizer.py        # Refinement
│   │   ├── validator.py          # Citation validation
│   │   └── context.py            # Agent context
│   ├── workflow/                 # Pipeline logic
│   │   ├── graph.py              # Research pipeline
│   │   ├── session.py            # Session management
│   │   └── memory.py             # Artifact storage
│   ├── tools/                    # Search & scraping
│   │   ├── search/               # Search tools (Tavily, Serper)
│   │   └── scrape.py             # Web scraping
│   ├── schemas/                  # Data models
│   └── prompts/                  # Agent prompts
│       ├── agents/               # Agent instructions
│       └── formats/              # Output templates
├── data/                         # Generated outputs
├── requirements.txt              # Dependencies
└── pyproject.toml                # Project config
```

---
