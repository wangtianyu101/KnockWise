"""Quick test of the Agent engine without needing a full server."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from agents.question_agent import question_engine
from agents.followup_agent import followup_engine
from agents.evaluate_agent import evaluate_agent
from agents.report_agent import report_agent


async def test_agent_engine():
    print("=" * 60)
    print("KnockWise Agent Engine Test")
    print("=" * 60)

    # 1. Test question selection
    print("\n--- 1. Question Selection ---")
    profile = {
        "tech_stack": ["LangChain", "LangGraph", "RAG"],
        "years_of_exp": 3,
        "current_level": "mid",
    }
    q = question_engine.select_next_question(
        round="round1", profile=profile, questions_asked=[], blind_spots=[]
    )
    print(f"Selected: [{q['topic']}] {q['question_text'][:80]}...")

    # 2. Test followup engine
    print("\n--- 2. Followup Engine ---")
    followup_result = await followup_engine.determine_action(
        question=q,
        user_answer="ReAct 模式就是 Thought-Action-Observation 的循环，LLM 先思考再行动，然后观察结果。",
        current_depth=0,
        followup_count=0,
        max_depth=4,
    )
    print(f"Action: {followup_result['action']}")
    print(f"Followup: {followup_result.get('followup_text', 'N/A')[:100]}")

    # 3. Test evaluation
    print("\n--- 3. Answer Evaluation ---")
    eval_result = await evaluate_agent.evaluate_answer(
        question_text=q["question_text"],
        answer_key_points=q.get("answer_key_points", []),
        user_answer="ReAct 模式就是 Thought-Action-Observation 的循环，LLM 先思考再行动，然后观察结果。",
        topic=q.get("topic", ""),
        sub_topic=q.get("sub_topic", ""),
    )
    print(f"Score: {eval_result['score']}/5")
    print(f"Blind spots: {eval_result['blind_spots']}")

    # 4. Test report generation
    print("\n--- 4. Report Generation ---")
    report = await report_agent.generate_report(
        profile=profile,
        questions_asked=[],
        blind_spots=["agent_basics"],
        total_score=3.5,
        round="round1",
    )
    print(f"Overall score: {report['overall_score']}")
    print(f"Summary: {report['summary'][:120]}")

    print("\n" + "=" * 60)
    print("All Agent tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_agent_engine())
