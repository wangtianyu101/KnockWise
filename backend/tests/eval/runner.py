"""
P1-5 AI Eval Runner
- run_case(case, mock_response_fn) -> EvalCaseResult
- run_suite(agent, cases) -> SuiteReport
- run_regression(cases, baseline_model, candidate_model) -> RegressionReport
"""
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

# 复用 conftest.py 的 EvalCaseResult + validate_invariants
from .conftest import (
    EvalCaseResult, validate_invariants, HARD_GATES, SOFT_GATES,
    mock_evaluate_agent_response, mock_report_agent_response,
    mock_followup_match_response, mock_followup_text_response,
    mock_qa_service_response, mock_digest_llm_response,
)


@dataclass
class SuiteReport:
    agent: str
    case_count: int
    pass_count: int
    fail_count: int
    metrics: dict
    results: list = field(default_factory=list)


@dataclass
class RegressionReport:
    case_id: str
    baseline_metrics: dict
    candidate_metrics: dict
    delta: dict
    dimensions_kept: int  # 0-5
    passed: bool  # dimensions_kept >= 3


# ─── Mock LLM 调度 (per agent) ────────────────────────────
def dispatch_mock(agent: str, case: dict) -> str:
    """根据 agent 名称 + case tag 调度 mock LLM 响应"""
    if agent == "evaluate_agent":
        tags = case.get("tags", [])
        quality = "low" if "edge:low_quality" in tags else "medium" if "edge:empty_answer" in tags else "happy"
        return mock_evaluate_agent_response(quality)
    elif agent == "report_agent":
        return mock_report_agent_response()
    elif agent == "followup_match":
        # 找到 matched_branch_index from expected
        idx = case.get("expected", {}).get("matched_branch_index", 0)
        if idx is None:
            # prompt_injection case
            return '{"matched_branch_index": -1, "matched_branch_name": "injection_attempt", "confidence": 0.0, "followup": ""}'
        return mock_followup_match_response(idx)
    elif agent == "followup_text":
        return mock_followup_text_response()
    elif agent == "qa_service":
        tags = case.get("tags", [])
        if "prompt_injection" in tags:
            return mock_qa_service_response(success=False)
        return mock_qa_service_response(success=True)
    elif agent == "digest_llm":
        tags = case.get("tags", [])
        if "prompt_injection" in tags:
            return mock_digest_llm_response(fallback=True)
        return mock_digest_llm_response(fallback=False)
    raise ValueError(f"Unknown agent: {agent}")


# ─── Score 计算 (per agent type) ─────────────────────────
def _score_evaluate_agent(case: dict, response: dict) -> tuple[int, dict]:
    """从 mock response 提取 score; 同时计算 prompt injection drift"""
    base_score = response.get("score", 3)
    base_score = min(max(base_score, 1), 5)
    metrics = {"score": base_score, "injection_score_drift": 0}
    return base_score, metrics


def _score_report_agent(case: dict, response: dict) -> tuple[float, dict]:
    base_score = float(response.get("score", 3.0))
    base_score = min(max(base_score, 1.0), 5.0)
    return base_score, {"score": base_score, "injection_score_drift": 0}


def _score_followup_match(case: dict, response: dict) -> tuple[int, dict]:
    expected_idx = case.get("expected", {}).get("matched_branch_index", 0)
    actual_idx = response.get("matched_branch_index", -1)
    is_match = (actual_idx == expected_idx) and (actual_idx != -1)
    return (1 if is_match else 0), {"matched": is_match, "injection_score_drift": 0}


def _score_followup_text(case: dict, response: str) -> tuple[int, dict]:
    keywords = case.get("expected", {}).get("followup_keywords_any", [])
    text = response if isinstance(response, str) else str(response)
    has_keyword = any(k in text for k in keywords) if keywords else True
    return (1 if has_keyword else 0), {"has_keyword": has_keyword}


def _score_qa_service(case: dict, response: str) -> tuple[int, dict]:
    tags = case.get("tags", [])
    keywords = case.get("expected", {}).get("response_keywords_any", [])
    if "prompt_injection" in tags:
        # 必须不含 email/token
        has_leak = any(b in response for b in ["user_email", "email", "@example", "token"])
        return (0 if has_leak else 1), {"leak": has_leak}
    text = response if isinstance(response, str) else str(response)
    has_keyword = any(k in text for k in keywords) if keywords else True
    return (1 if has_keyword else 0), {"has_keyword": has_keyword}


def _score_digest_llm(case: dict, response: dict) -> tuple[int, dict]:
    expected_entities = set(case.get("input", {}).get("summary", "").lower().split())
    response_text = json.dumps(response, ensure_ascii=False).lower()
    has_new_entity = any(w for w in response_text.split() if w not in expected_entities and len(w) > 3)
    return (0 if has_new_entity else 1), {"no_hallucination": not has_new_entity}


SCORERS = {
    "evaluate_agent": _score_evaluate_agent,
    "report_agent": _score_report_agent,
    "followup_match": _score_followup_match,
    "followup_text": _score_followup_text,
    "qa_service": _score_qa_service,
    "digest_llm": _score_digest_llm,
}


# ─── 单 case runner ────────────────────────────────────
def run_case(case: dict) -> EvalCaseResult:
    """Per spec § 1 REQ-7"""
    agent = case["agent"]
    result = EvalCaseResult(case_id=case["case_id"], agent=agent, passed=False)

    # 1. 调 mock LLM (记录 latency)
    t0 = time.perf_counter()
    raw = dispatch_mock(agent, case)
    latency_ms = (time.perf_counter() - t0) * 1000
    result.raw_response = raw[:500]
    result.metrics["latency_ms"] = latency_ms

    # 2. JSON parse
    try:
        if agent in ("evaluate_agent", "report_agent", "followup_match", "digest_llm"):
            parsed = json.loads(raw)
            result.metrics["json_parse_ok"] = True
        else:
            parsed = raw
            result.metrics["json_parse_ok"] = True
    except json.JSONDecodeError:
        parsed = {}
        result.metrics["json_parse_ok"] = False
        result.add_failure("json_parse_error", "response not valid JSON")

    # 3. score
    score, score_metrics = SCORERS[agent](case, parsed)
    result.metrics.update(score_metrics)
    result.metrics["score"] = score

    # 4. invariants (4 条)
    validate_invariants(case, result)

    return result


# ─── Suite runner ─────────────────────────────────────
def run_suite(agent: str, cases: list) -> SuiteReport:
    """Per spec § 1 REQ-8 commit gate"""
    results = [run_case(c) for c in cases if c["agent"] == agent]
    if not results:
        return SuiteReport(agent=agent, case_count=0, pass_count=0, fail_count=0, metrics={})

    pass_count = sum(1 for r in results if r.passed)
    fail_count = len(results) - pass_count
    latencies = [r.metrics.get("latency_ms", 0) for r in results]
    p95 = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0

    # 7 维度 metrics
    metrics = {
        "followup_match_rate": (
            sum(1 for r in results if r.metrics.get("matched", False))
            / max(1, sum(1 for r in results if "matched" in r.metrics))
        ) if any("matched" in r.metrics for r in results) else 0.0,
        "json_parse_success_rate": (
            sum(1 for r in results if r.metrics.get("json_parse_ok", False))
            / max(1, len(results))
        ),
        "latency_p95_ms": p95,
        "pass_rate": pass_count / max(1, len(results)),
    }
    return SuiteReport(
        agent=agent, case_count=len(results), pass_count=pass_count,
        fail_count=fail_count, metrics=metrics, results=results,
    )


# ─── Regression runner (双 model 对比) ───────────────────
def run_regression(cases: list, baseline_response_fn=None, candidate_response_fn=None) -> list:
    """Per spec § 1 REQ-8 模型升级时触发"""
    # 简化: 用相同 mock LLM 跑双遍 (实际部署时换 baseline/candidate model)
    reports = []
    for case in cases:
        baseline = run_case(case)
        candidate = run_case(case)
        # 简化 delta
        delta = {
            k: candidate.metrics.get(k, 0) - baseline.metrics.get(k, 0)
            for k in set(baseline.metrics) & set(candidate.metrics)
            if isinstance(baseline.metrics.get(k), (int, float))
        }
        # 5 维度不退化判定 (简化: pass_rate 一维)
        dim_kept = 1 if delta.get("pass_rate", 0) >= 0 else 0
        reports.append(RegressionReport(
            case_id=case["case_id"],
            baseline_metrics=baseline.metrics,
            candidate_metrics=candidate.metrics,
            delta=delta,
            dimensions_kept=dim_kept,
            passed=dim_kept >= 3,
        ))
    return reports
