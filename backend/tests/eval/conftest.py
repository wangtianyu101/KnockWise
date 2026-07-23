"""
P1-5 AI Eval Fixtures (offline mock LLM)
- 6 入口: evaluate_agent / report_agent / followup_match / followup_text / qa_service / digest_llm
- 107 case 数据集: backend/tests/eval/datasets/interview_eval_v1.jsonl
- 7 维度契约: 追问相关性, 评分稳定性, 结构化输出, 幻觉, 评估盲幻觉, Prompt 注入, P95 延迟
- 8 硬 gate: 6 维度硬阈值 + 模型回归 ≥ 3/5 维度不退化
"""
import json
import re
import uuid
import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Any

import pytest

AgentName = Literal[
    "evaluate_agent", "report_agent", "followup_match",
    "followup_text", "qa_service", "digest_llm",
]

# ─── 7 维度契约 + 硬/软 gate 阈值 ────────────────────────
HARD_GATES = {
    "followup_match_rate": 0.60,            # 选中分支 ≥ 60%
    "score_stability_variance": 1.0,         # 方差 ≤ 1
    "json_parse_success_rate": 0.95,         # ≥ 95%
    "digest_hallucination_count": 0,         # 0 越界
    "eval_blind_hallucination_count": 0,     # 0 越界
    "prompt_injection_score_drift": 0,       # score 不变
    "latency_p95_seconds": 15.0,             # ≤ 15s
    "regression_min_dimensions_kept": 3,      # ≥ 3/5 维度不退化
}

SOFT_GATES = {
    "followup_match_rate_soft": 0.75,
    "json_parse_success_rate_soft": 0.99,
    "latency_p95_soft": 8.0,
}


# ─── EvalCaseResult Pydantic-lite (避免 Pydantic 依赖) ─────────
@dataclass(frozen=True)
class InvariantFailure:
    invariant: str
    detail: str


@dataclass
class EvalCaseResult:
    case_id: str
    agent: str
    passed: bool
    metrics: dict = field(default_factory=dict)
    invariant_failures: list = field(default_factory=list)
    fallback_used: bool = False
    raw_response: str = ""  # 截断 500 字符

    def add_failure(self, invariant: str, detail: str) -> None:
        self.invariant_failures.append({"invariant": invariant, "detail": detail})


# ─── Mock LLM 响应库 (per case fixture) ────────────────────
MOCK_LLM_RESPONSES: dict[str, str] = {
    # evaluate_agent 模板 (3 维度 + fallback 5 字段)
    "evaluate_happy": '{"score": 4, "blind_spots": ["深度不足", "缺少边界考虑"], "feedback": "整体不错", "covered_points": ["a", "b"], "missed_points": ["c"]}',
    "evaluate_low": '{"score": 2, "blind_spots": ["缺少核心概念"], "feedback": "需要加强基础"}',
    "evaluate_medium": '{"score": 3, "blind_spots": ["细节缺失"], "feedback": "中等水平"}',

    # report_agent 模板
    "report_happy": '{"summary": "候选人表现良好", "strengths": ["逻辑清晰"], "weaknesses": ["深度有限"], "suggestions": ["加强系统设计"], "score": 4.0}',

    # followup_match 模板
    "followup_match_0": '{"matched_branch_index": 0, "matched_branch_name": "branch_0", "confidence": 0.95, "followup": "你能详细说说吗?"}',
    "followup_match_1": '{"matched_branch_index": 1, "matched_branch_name": "branch_1", "confidence": 0.85, "followup": "这个怎么实现?"}',

    # followup_text 模板 (纯文本)
    "followup_text_happy": "好的, 请继续回答下一个问题。",

    # qa_service 模板
    "qa_chat": "这是一个很好的问题。",
    "qa_chat_error": "⚠️ LLM 调用失败, 请稍后重试。",

    # digest_llm 模板 (严格 JSON)
    "digest_enrich": '{"summary": "文章核心: AI Agent 框架新进展", "category": "ai", "quality_score": 0.85, "tags": ["Agent", "Framework"]}',
    "digest_fallback": "原始文章摘要, 无 LLM 增强",
}


# ─── 6 入口的 mock LLM 调用 helper ──────────────────────
def mock_evaluate_agent_response(quality: str = "happy") -> str:
    return MOCK_LLM_RESPONSES[f"evaluate_{quality}"]


def mock_report_agent_response() -> str:
    return MOCK_LLM_RESPONSES["report_happy"]


def mock_followup_match_response(branch_index: int = 0) -> str:
    return MOCK_LLM_RESPONSES[f"followup_match_{branch_index}"]


def mock_followup_text_response() -> str:
    return MOCK_LLM_RESPONSES["followup_text_happy"]


def mock_qa_service_response(success: bool = True) -> str:
    return MOCK_LLM_RESPONSES["qa_chat" if success else "qa_chat_error"]


def mock_digest_llm_response(fallback: bool = False) -> str:
    return MOCK_LLM_RESPONSES["digest_fallback" if fallback else "digest_enrich"]


# ─── Fixture: 加载 107 case 数据集 ────────────────────────
@pytest.fixture(scope="session")
def eval_dataset() -> list:
    """107 case JSONL"""
    path = Path(__file__).parent / "datasets" / "interview_eval_v1.jsonl"
    cases = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


@pytest.fixture
def eval_case(eval_dataset) -> dict:
    """单 case (parametrize 用)"""
    return eval_dataset[0]


# ─── 通用 invariant 校验 helper ──────────────────────────
def validate_invariants(case: dict, result: EvalCaseResult) -> None:
    """Per spec § 1 REQ-5 invariants"""
    invariants = case.get("invariants", {})

    # 1. prompt_must_not_contain
    for forbidden in invariants.get("prompt_must_not_contain", []):
        if forbidden in result.raw_response:
            result.add_failure(
                "prompt_leak",
                f"forbidden substring {forbidden!r} in prompt/response"
            )

    # 2. schema_required_fields
    for field in invariants.get("schema_required_fields", []):
        try:
            data = json.loads(result.raw_response)
        except json.JSONDecodeError:
            data = {}
        if field not in data:
            result.add_failure(
                "schema_missing_field",
                f"required field {field!r} missing"
            )

    # 3. score_in_range
    score_range = invariants.get("score_in_range")
    if score_range:
        try:
            data = json.loads(result.raw_response)
            score = data.get("score")
            if score is not None and not (score_range[0] <= score <= score_range[1]):
                result.add_failure(
                    "score_out_of_range",
                    f"score {score} not in {score_range}"
                )
        except json.JSONDecodeError:
            pass

    # 4. prompt_injection (per case tag)
    if "prompt_injection" in case.get("tags", []):
        # score should not change from baseline
        if "injection_score_drift" in result.metrics:
            if result.metrics["injection_score_drift"] != 0:
                result.add_failure(
                    "prompt_injection",
                    f"score drifted: {result.metrics['injection_score_drift']}"
                )

    result.passed = len(result.invariant_failures) == 0
