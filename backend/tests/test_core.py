"""Unit tests for KnockWise core components: states, questions, followup, seed data.

Run: python -m pytest tests/ -v
"""

import json
import pytest
from pathlib import Path

SEED_DIR = Path(__file__).parent.parent / "seed_data"


# ===== Test States =====

class TestInterviewState:
    def test_create_initial_state_has_required_fields(self):
        from agents.states import create_initial_state

        state = create_initial_state(
            user_id="test_user",
            profile={"tech_stack": ["Python"]},
            round="round1",
        )

        assert state["user_id"] == "test_user"
        assert state["round"] == "round1"
        assert state["interview_phase"] == "intro"
        assert state["should_end"] is False
        assert state["current_depth"] == 0
        assert state["followup_count"] == 0
        assert state["max_followup_depth"] == 4
        assert state["questions_asked"] == []
        assert state["blind_spots"] == []
        assert state["messages"] == []

    def test_state_fields_are_typed(self):
        from agents.states import InterviewState

        # Verify the TypedDict has all required keys
        required_keys = [
            "user_id", "profile", "round", "style",
            "current_topic", "current_question_id", "current_question",
            "current_depth", "user_answer", "answer_evaluation",
            "questions_asked", "questions_remaining", "total_score", "blind_spots",
            "messages", "interview_phase", "route", "should_end",
            "followup_count", "max_followup_depth",
        ]
        # Just verify the class exists and has annotations
        assert hasattr(InterviewState, "__annotations__")
        for key in required_keys:
            assert key in InterviewState.__annotations__, f"Missing key: {key}"


# ===== Test Question Engine =====

class TestQuestionEngine:
    def test_load_all_questions(self):
        from agents.question_agent import question_engine
        assert len(question_engine.all_questions) >= 50, f"Expected >=50, got {len(question_engine.all_questions)}"

    def test_select_question_filters_by_round(self):
        from agents.question_agent import question_engine

        q = question_engine.select_next_question(
            round="round1",
            profile={"tech_stack": [], "years_of_exp": 1, "current_level": "junior"},
            questions_asked=[],
            blind_spots=[],
        )
        assert q is not None
        assert "id" in q
        assert "question_text" in q
        assert "topic" in q
        assert "followup_tree" in q

    def test_select_question_avoids_duplicates(self):
        from agents.question_agent import question_engine

        # Ask 10 questions, then verify the 11th is different from all previous
        asked = []
        for _ in range(10):
            q = question_engine.select_next_question(
                round="round1",
                profile={"tech_stack": [], "years_of_exp": 3, "current_level": "mid"},
                questions_asked=asked,
                blind_spots=[],
            )
            if q:
                assert q["id"] not in asked
                asked.append(q["id"])

    def test_select_question_prioritizes_tech_stack(self):
        from agents.question_agent import question_engine

        q = question_engine.select_next_question(
            round="round1",
            profile={"tech_stack": ["Java"], "years_of_exp": 1, "current_level": "junior"},
            questions_asked=[],
            blind_spots=[],
        )
        assert q is not None
        # With Java in profile, should get a Java question (or at least a valid q)
        assert q["topic"] in ("java", "agent_architecture", "rag", "langchain", "langgraph")

    def test_get_question_by_id_returns_correct_question(self):
        from agents.question_agent import question_engine

        q = question_engine.get_question_by_id("agent_001")
        assert q is not None
        assert q["id"] == "agent_001"
        assert "ReAct" in q["question_text"]

    def test_get_nonexistent_question_returns_none(self):
        from agents.question_agent import question_engine

        q = question_engine.get_question_by_id("nonexistent_999")
        assert q is None


# ===== Test Followup Engine (no LLM calls) =====

class TestFollowupEngine:
    def test_engine_instantiates(self):
        from agents.followup_agent import FollowupEngine
        engine = FollowupEngine()
        assert engine is not None
        assert engine.llm is not None

    def test_make_action_returns_valid_dict(self):
        from agents.followup_agent import FollowupEngine
        engine = FollowupEngine()
        result = engine._make_action("next_question", score=3)
        assert result["action"] == "next_question"
        assert result["score"] == 3
        assert result["depth"] == 0

    def test_calculate_score_maps_actions(self):
        from agents.followup_agent import FollowupEngine
        engine = FollowupEngine()

        assert engine._calculate_score({"action": "skip_and_record"}, []) == 1
        assert engine._calculate_score({"action": "give_hint"}, []) == 2
        assert engine._calculate_score({"action": "degrade"}, []) == 2
        assert engine._calculate_score({"action": "probe"}, []) == 3
        assert engine._calculate_score({"action": "followup", "depth": 2}, []) == 5

    def test_calculate_score_uses_explicit_score(self):
        from agents.followup_agent import FollowupEngine
        engine = FollowupEngine()
        assert engine._calculate_score({"action": "followup", "score": 1}, []) == 1
        assert engine._calculate_score({"action": "skip_and_record", "score": 5}, []) == 5

    def test_quick_score_empty_answer(self):
        from agents.followup_agent import FollowupEngine
        engine = FollowupEngine()
        assert engine._quick_score("", []) == 1       # too short
        assert engine._quick_score("ab", []) == 1     # too short
        assert engine._quick_score("a" * 500, []) == 3  # no answer_key → return 3
        assert engine._quick_score("a" * 500, ["point1"]) == 4  # 2 + 500//200 = 4

    def test_keyword_fallback_matches_condition_text(self):
        from agents.followup_agent import FollowupEngine
        engine = FollowupEngine()

        branches = [
            {"condition": "答出完整循环且有例子", "action": "followup", "followup": "继续"},
            {"condition": "完全不会", "action": "skip_and_record"},
        ]
        result = engine._keyword_fallback(branches, "我完全不会这个题")
        assert result["action"] in ("skip_and_record", "followup")

    def test_keyword_fallback_prefers_non_skip(self):
        from agents.followup_agent import FollowupEngine
        engine = FollowupEngine()

        branches = [
            {"condition": "xyz_unknown_pattern", "action": "skip_and_record"},
            {"condition": "another_unknown", "action": "degrade"},
        ]
        # Should pick degrade (non-skip) even though no keywords match
        result = engine._keyword_fallback(branches, "something completely different")
        assert result["action"] == "degrade"

    def test_no_followup_tree_moves_on(self):
        from agents.followup_agent import FollowupEngine
        import asyncio

        engine = FollowupEngine()
        result = asyncio.run(engine.determine_action(
            question={"question_text": "test", "followup_tree": {}},
            user_answer="anything",
            current_depth=0,
            followup_count=0,
        ))
        assert result["action"] == "next_question"

    def test_max_depth_moves_on(self):
        from agents.followup_agent import FollowupEngine
        import asyncio

        engine = FollowupEngine()
        result = asyncio.run(engine.determine_action(
            question={
                "question_text": "test",
                "followup_tree": {"branches": [{"condition": "any", "action": "followup"}]},
                "answer_key_points": ["point1"],
            },
            user_answer="some answer",
            current_depth=4,  # at max
            followup_count=3,  # at max
            max_depth=4,
        ))
        assert result["action"] == "next_question"


# ===== Test Seed Data =====

class TestSeedData:
    SEED_FILES = ["agent_core.json", "rag_tech.json", "langgraph.json", "java_backend.json"]

    def test_all_seed_files_exist(self):
        for fname in self.SEED_FILES:
            assert (SEED_DIR / fname).exists(), f"Missing: {fname}"

    def test_all_questions_are_valid_json(self):
        for fname in self.SEED_FILES:
            data = json.loads((SEED_DIR / fname).read_text())
            assert isinstance(data, list), f"{fname}: not a list"
            assert len(data) > 0, f"{fname}: empty"

    def test_question_ids_are_unique(self):
        all_ids = []
        for fname in self.SEED_FILES:
            data = json.loads((SEED_DIR / fname).read_text())
            for q in data:
                assert q["id"] not in all_ids, f"Duplicate ID: {q['id']}"
                all_ids.append(q["id"])

    def test_total_question_count(self):
        total = 0
        for fname in self.SEED_FILES:
            data = json.loads((SEED_DIR / fname).read_text())
            total += len(data)
        assert total == 50, f"Expected 50 questions, got {total}"

    def test_each_question_has_required_fields(self):
        required = ["id", "topic", "sub_topic", "difficulty", "round", "question_text", "followup_tree"]
        for fname in self.SEED_FILES:
            data = json.loads((SEED_DIR / fname).read_text())
            for q in data:
                for field in required:
                    assert field in q, f"{fname}/{q.get('id', '?')}: missing {field}"

    def test_followup_trees_have_branches(self):
        for fname in self.SEED_FILES:
            data = json.loads((SEED_DIR / fname).read_text())
            for q in data:
                tree = q.get("followup_tree", {})
                assert "branches" in tree, f"{q['id']}: followup_tree missing branches"
                assert isinstance(tree["branches"], list), f"{q['id']}: branches not a list"
                assert len(tree["branches"]) >= 1, f"{q['id']}: empty branches"

    def test_difficulty_ranges_are_valid(self):
        for fname in self.SEED_FILES:
            data = json.loads((SEED_DIR / fname).read_text())
            for q in data:
                assert 1 <= q["difficulty"] <= 5, f"{q['id']}: invalid difficulty {q['difficulty']}"

    def test_round_values_are_valid(self):
        for fname in self.SEED_FILES:
            data = json.loads((SEED_DIR / fname).read_text())
            for q in data:
                assert q["round"] in ("round1", "round2"), f"{q['id']}: invalid round {q['round']}"

    def test_topic_coverage(self):
        topics = set()
        for fname in self.SEED_FILES:
            data = json.loads((SEED_DIR / fname).read_text())
            for q in data:
                topics.add(q["topic"])
        expected = {"agent_architecture", "rag", "langgraph", "langchain", "java"}
        assert topics == expected, f"Expected {expected}, got {topics}"


# ===== Test Seed Service =====

class TestSeedService:
    def test_load_questions_from_files(self):
        from services.seed_service import load_questions_from_files
        questions = load_questions_from_files()
        assert len(questions) == 50

    def test_get_question_by_id(self):
        from services.seed_service import get_question_by_id
        q = get_question_by_id("lang_004")
        assert q is not None
        assert q["id"] == "lang_004"

    def test_get_questions_by_topic(self):
        from services.seed_service import get_questions_by_topic
        qs = get_questions_by_topic("java")
        assert len(qs) == 5
        assert all(q["topic"] == "java" for q in qs)
