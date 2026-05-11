"""LangGraph Interview State definitions."""

from typing import Annotated
from typing_extensions import TypedDict
import operator


class InterviewState(TypedDict):
    # === User & Profile ===
    user_id: str
    profile: dict  # {tech_stack, years_of_exp, current_level, target_companies, resume_summary, skill_map}

    # === Interview Config ===
    round: str  # "round1" | "round2"
    style: str  # "standard"

    # === Current Question State ===
    current_topic: str
    current_question_id: str
    current_question: dict  # full question object with followup_tree
    current_depth: int  # current followup depth (1-4)
    user_answer: str
    answer_evaluation: dict  # {score: int, matched_branch: str, blind_spots: list}

    # === Progress Tracking ===
    questions_asked: Annotated[list, operator.add]  # accumulated question IDs
    questions_remaining: list[str]  # question IDs yet to ask
    total_score: float
    blind_spots: Annotated[list, operator.add]  # accumulated blind spots

    # === Conversation ===
    messages: Annotated[list, operator.add]  # full conversation log

    # === Control ===
    interview_phase: str  # "intro" | "questioning" | "following_up" | "done"
    route: str  # routing decision: "followup" | "next_question" | "report"
    should_end: bool
    followup_count: int  # number of followups asked for current question
    max_followup_depth: int  # max followup depth (default 4)


def create_initial_state(
    user_id: str,
    profile: dict,
    round: str = "round1",
    style: str = "standard",
) -> InterviewState:
    """Create the initial interview state."""
    return InterviewState(
        user_id=user_id,
        profile=profile,
        round=round,
        style=style,
        current_topic="",
        current_question_id="",
        current_question={},
        current_depth=0,
        user_answer="",
        answer_evaluation={},
        questions_asked=[],
        questions_remaining=[],
        total_score=0.0,
        blind_spots=[],
        messages=[],
        interview_phase="intro",
        route="",
        should_end=False,
        followup_count=0,
        max_followup_depth=4,
    )
