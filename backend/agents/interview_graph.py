"""Main Interview Graph — orchestrates the full interview flow using LangGraph.

Nodes:
  select_question → ask → receive → evaluate_route → followup/report
"""

from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents.states import InterviewState
from agents.question_agent import question_engine
from agents.followup_agent import followup_engine
from agents.evaluate_agent import evaluate_agent
from agents.report_agent import report_agent


# ===== Node Functions =====

async def select_next_question(state: InterviewState) -> dict:
    """Select the next question based on interview context."""
    next_q = question_engine.select_next_question(
        round=state["round"],
        profile=state["profile"],
        questions_asked=state["questions_asked"],
        blind_spots=state["blind_spots"],
        current_topic=state.get("current_topic"),
    )

    if not next_q:
        # No more questions
        return {
            "should_end": True,
            "interview_phase": "done",
        }

    return {
        "current_question_id": next_q["id"],
        "current_question": next_q,
        "current_topic": next_q.get("topic", ""),
        "current_depth": 0,
        "followup_count": 0,
        "interview_phase": "questioning",
        "questions_asked": [next_q["id"]],
        "messages": [{
            "role": "interviewer",
            "type": "question",
            "content": next_q["question_text"],
        }],
    }


async def ask_question(state: InterviewState) -> dict:
    """Return the current question text for TTS.

    This node is a pass-through — the question text is already in state.
    In the voice pipeline, this is where TTS would be triggered.
    """
    return {}


async def receive_answer(state: InterviewState) -> dict:
    """Pass-through node — user answer is written to state externally before this node runs."""
    return {}


async def evaluate_answer(state: InterviewState) -> dict:
    """Evaluate the user's answer and determine the next routing action.

    All state mutations happen here (inside a proper node), not in the routing function.
    Returns routing decision via the "route" key in returned dict.
    """
    if state.get("should_end"):
        return {"interview_phase": "done", "route": "report"}

    if state["interview_phase"] == "done":
        return {"route": "report"}

    # Check question count limits
    if len(state["questions_asked"]) >= 8 and state.get("round") == "round1":
        return {"interview_phase": "done", "route": "report"}

    if len(state["questions_asked"]) >= 5 and state.get("round") == "round2":
        return {"interview_phase": "done", "route": "report"}

    current_question = state.get("current_question", {})
    user_answer = state.get("user_answer", "")

    if not user_answer:
        return {"route": "next_question"}

    # Use followup engine to determine action
    result = await followup_engine.determine_action(
        question=current_question,
        user_answer=user_answer,
        current_depth=state.get("current_depth", 0),
        followup_count=state.get("followup_count", 0),
        max_depth=state.get("max_followup_depth", 4),
    )

    action = result.get("action", "next_question")

    if action in ("skip_and_record", "next_question"):
        return {
            "answer_evaluation": {
                "score": result.get("score", 3),
                "action": action,
                "blind_spots": [result.get("blind_spot", "")] if result.get("blind_spot") else [],
            },
            "route": "next_question",
        }

    # followup, probe, give_hint, degrade
    return {
        "followup_count": state.get("followup_count", 0) + 1,
        "current_depth": result.get("depth", state.get("current_depth", 0) + 1),
        "answer_evaluation": {
            "score": result.get("score", 3),
            "action": action,
            "followup_text": result.get("followup_text", ""),
        },
        "interview_phase": "following_up",
        "route": "followup",
    }


def route_after_evaluate(state: InterviewState) -> Literal["followup", "next_question", "report"]:
    """Pure routing function — reads state, returns destination node name. Never mutates."""
    return state.get("route", "next_question")


async def generate_followup(state: InterviewState) -> dict:
    """Generate and append the followup question."""
    eval_data = state.get("answer_evaluation", {})
    followup_text = eval_data.get("followup_text", "能再详细说说吗？")

    msg = {
        "role": "interviewer",
        "type": "followup",
        "content": followup_text,
        "depth": state.get("current_depth", 0),
    }

    return {
        "interview_phase": "following_up",
        "messages": [msg],
    }


async def generate_report(state: InterviewState) -> dict:
    """Generate the final interview report."""
    result = await report_agent.generate_report(
        profile=state["profile"],
        blind_spots=state["blind_spots"],
        total_score=state.get("total_score", 0),
        round=state["round"],
        questions_asked=[{k: state.get(k) for k in ["current_question_id", "current_topic", "user_answer"]}],
    )

    return {
        "interview_phase": "done",
        "messages": [{
            "role": "system",
            "type": "report",
            "content": result.get("summary", "面试报告已生成。"),
            "report_data": result,
        }],
    }


# ===== Build Graph =====

def build_interview_graph() -> StateGraph:
    """Build and compile the interview LangGraph."""
    workflow = StateGraph(InterviewState)

    # Add nodes
    workflow.add_node("select_question", select_next_question)
    workflow.add_node("ask", ask_question)
    workflow.add_node("receive", receive_answer)
    workflow.add_node("evaluate", evaluate_answer)
    workflow.add_node("followup", generate_followup)
    workflow.add_node("report", generate_report)

    # Set entry
    workflow.set_entry_point("select_question")

    # Edges
    workflow.add_edge("select_question", "ask")
    workflow.add_edge("ask", "receive")
    workflow.add_edge("receive", "evaluate")

    # Conditional routing: evaluate node writes "route" to state, router reads it
    workflow.add_conditional_edges(
        "evaluate",
        route_after_evaluate,
        {
            "followup": "followup",
            "next_question": "select_question",
            "report": "report",
        },
    )

    workflow.add_edge("followup", "ask")
    workflow.add_edge("report", END)

    # Compile with memory for checkpointing
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
    return graph


# Singleton graph instance with checkpointing
interview_graph = build_interview_graph()
