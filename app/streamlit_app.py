import streamlit as st
import asyncio
import logging
import threading
import time
import json
from pathlib import Path
from queue import Queue
from typing import Any, Dict
from datetime import datetime

from core.settings import get_settings
from workflow.graph import ResearchPipeline
from schemas.research import ResearchInput
from schemas.tool_result import SourceCard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Deep Scout", page_icon="🔍", layout="wide")

if "research_started" not in st.session_state:
    st.session_state.research_started = False
    st.session_state.results = {}
    st.session_state.result_queue = None


def depth_to_iterations(depth: str) -> int:
    mapping = {"basic": 2, "intermediate": 3, "deep": 5}
    return mapping.get(depth, 3)


def run_in_thread(topic: str, purpose: str, depth: str, output_format: str, result_queue: Queue):
    async def run():
        settings = get_settings()
        pipeline = ResearchPipeline(settings, use_planner=True)

        research_input = ResearchInput(
            topic=topic,
            purpose=purpose,
            depth=depth,
            output_format=output_format,
            custom_instructions="",
        )

        state = {
            "topic": topic,
            "purpose": purpose,
            "depth": depth,
            "output_format": output_format,
            "custom_instructions": "",
            "max_iterations": depth_to_iterations(depth),
            "iteration": 0,
            "research_transcript": "",
            "sources": [],
        }

        max_iterations = state["max_iterations"]

        result_queue.put({"step": "planning", "message": "Creating research plan...", "progress": 0.05})
        plan = await pipeline.planner.run(research_input)
        state["subtopics"] = plan.subtopics
        state["search_queries"] = plan.search_queries
        result_queue.put({
            "step": "plan_ready",
            "message": "Research plan created",
            "progress": 0.1,
            "subtopics": plan.subtopics,
            "queries": plan.search_queries,
        })

        while state.get("iteration", 0) < max_iterations:
            current_round = state.get("iteration", 0) + 1
            result_queue.put({
                "step": "research",
                "message": f"Research round {current_round}/{max_iterations}...",
                "progress": 0.1 + (0.5 * (current_round - 1) / max_iterations),
                "round": current_round,
                "total_rounds": max_iterations,
            })

            update = await pipeline.scout.run(state)
            state.update(update)

            sources_count = len(state.get("sources", []))
            result_queue.put({
                "step": "research_round_complete",
                "message": f"Round {current_round} complete - {sources_count} sources found",
                "progress": 0.1 + (0.5 * current_round / max_iterations),
                "round": current_round,
                "sources_found": sources_count,
            })

        result_queue.put({"step": "drafting", "message": "Generating draft...", "progress": 0.6})

        sources = [SourceCard.model_validate(d) for d in state.get("sources", [])]

        draft = await pipeline.draft_generator.run(
            topic=topic,
            purpose=purpose,
            output_format=output_format,
            scout_transcript=state.get("research_transcript", ""),
            sources=sources,
            custom_instructions="",
        )
        result_queue.put({
            "step": "draft_ready",
            "message": "Draft generated",
            "progress": 0.7,
            "draft_preview": draft[:1000],
        })

        result_queue.put({"step": "critiquing", "message": "Running critique...", "progress": 0.75})

        critique = await pipeline.critic.run(draft, topic=topic, purpose=purpose)
        result_queue.put({
            "step": "critique_ready",
            "message": "Critique complete",
            "progress": 0.8,
            "critique_score": critique.score,
            "issues_count": len(critique.issues),
            "improvements_count": len(critique.improvements),
        })

        result_queue.put({"step": "synthesizing", "message": "Synthesizing final output...", "progress": 0.85})

        final_draft = await pipeline.synthesizer.run(
            draft=draft,
            critique=critique,
            topic=topic,
            purpose=purpose,
            output_format=output_format,
            sources=sources,
        )

        result_queue.put({"step": "validating", "message": "Validating citations...", "progress": 0.9})

        validated_md, validation = pipeline.validator.validate(final_draft, sources)

        result_queue.put({
            "step": "complete",
            "message": "Research complete!",
            "progress": 1.0,
            "markdown": validated_md,
            "sources_count": len(sources),
            "critique_score": critique.score,
            "confidence_score": validation.confidence_score,
        })

    asyncio.run(run())


def main():
    st.title("🔍 Deep Scout")
    st.markdown("Research any topic with AI-powered deep research")

    with st.sidebar:
        st.header("Settings")
        purpose = st.selectbox("Purpose", ["learn", "write", "compare", "debug"], index=0)
        depth = st.select_slider("Depth", options=["basic", "intermediate", "deep"], value="intermediate")
        output_format = st.selectbox("Output Format", ["report", "tutorial", "explain", "comparison"], index=0)

    topic = st.text_input("Enter your research topic:", placeholder="e.g., How does quantum computing work?")

    if st.button("Start Research", type="primary") and topic:
        st.session_state.research_started = True
        st.session_state.results = {}
        st.session_state.result_queue = Queue()
        st.rerun()

    if st.session_state.research_started and not st.session_state.results:
        progress_bar = st.progress(0)
        status_text = st.empty()
        steps_container = st.container()

        result_queue = st.session_state.result_queue
        results = {}
        subtopics = []
        queries = []

        if not hasattr(st.session_state, 'research_thread') or not st.session_state.research_thread.is_alive():
            thread = threading.Thread(target=run_in_thread, args=(topic, purpose, depth, output_format, result_queue))
            st.session_state.research_thread = thread
            thread.start()

        while st.session_state.research_thread.is_alive():
            try:
                while not result_queue.empty():
                    event = result_queue.get_nowait()
                    progress_bar.progress(event["progress"])
                    status_text.markdown(f"**Status:** {event['message']}")

                    if event["step"] == "plan_ready":
                        subtopics = event.get("subtopics", [])
                        queries = event.get("queries", [])
                        with st.expander("📋 Research Plan", expanded=True):
                            st.write(f"**Subtopics:** {', '.join(subtopics)}")
                            st.write(f"**Search Queries:** {', '.join(queries)}")

                    elif event["step"] == "research_round_complete":
                        round_num = event.get("round", 0)
                        sources = event.get("sources_found", 0)
                        with st.expander(f"🔍 Research Round {round_num}", expanded=False):
                            st.write(f"Found {sources} sources")

                    elif event["step"] == "draft_ready":
                        draft_preview = event.get("draft_preview", "")
                        with st.expander("✍️ Draft Generated", expanded=True):
                            st.text(draft_preview + "...")

                    elif event["step"] == "critique_ready":
                        score = event.get("critique_score", 0)
                        issues = event.get("issues_count", 0)
                        improvements = event.get("improvements_count", 0)
                        with st.expander("⚖️ Critique Complete", expanded=True):
                            st.write(f"**Score:** {score}/10")
                            st.write(f"**Issues:** {issues}")
                            st.write(f"**Improvements:** {improvements}")

                    elif event["step"] == "complete":
                        results = event
                    elif event["step"] == "error":
                        st.error(f"Error: {event.get('message', 'Unknown error')}")
            except Exception as e:
                st.error(f"Processing error: {str(e)}")
            time.sleep(0.1)

        st.session_state.research_thread.join()

        while not result_queue.empty():
            event = result_queue.get_nowait()
            if event["step"] == "complete":
                results = event
            elif event["step"] == "error":
                st.error(f"Error: {event.get('message', 'Unknown error')}")

        st.session_state.results = results

    if st.session_state.results.get("markdown"):
        st.divider()
        results = st.session_state.results
        st.header("📄 Final Article")
        st.markdown(results["markdown"])

        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = data_dir / f"research_{timestamp}.json"
        output_data = {
            "topic": topic,
            "timestamp": timestamp,
            "markdown": results.get("markdown", ""),
            "sources_count": results.get("sources_count", 0),
            "critique_score": results.get("critique_score", 0),
            "confidence_score": results.get("confidence_score", 0),
        }
        json_path.write_text(json.dumps(output_data, indent=2))
        st.success(f"Results saved to {json_path}")

        with st.expander("Sources"):
            st.write(f"Total sources: {results.get('sources_count', 0)}")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Critique Score", f"{results.get('critique_score', 0)}/10")
        with col2:
            st.metric("Confidence", f"{results.get('confidence_score', 0):.2%}")


if __name__ == "__main__":
    main()