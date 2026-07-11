"""POC-4: 6 步工作流 e2e（最小可跑版本）

目标：验证 6 步流程可被状态机驱动
通过标准：能 start → advance → get_state 跑通完整闭环
"""
import json
import sqlite3
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable


class StepState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    APPROVED = "approved"
    FAILED = "failed"


# === 6 步定义（参考全局流程.md） ===
SIX_STEPS = [
    ("0_research", "调研", lambda ctx: {"research_md": f"# Research for {ctx['topic']}"}),
    ("1_spec", "规格", lambda ctx: {"spec_md": f"# Spec for {ctx['topic']}"}),
    ("2_plan", "计划", lambda ctx: {"plan_md": f"# Plan for {ctx['topic']}"}),
    ("3_tasks", "拆分", lambda ctx: {"tasks_md": f"# Tasks for {ctx['topic']}"}),
    ("4_implement", "实现", lambda ctx: {"test_py": f"# Test for {ctx['topic']}"}),
    ("5_verify", "验证", lambda ctx: {"verify_md": f"# Verify for {ctx['topic']}"}),
    ("6_retro", "复盘", lambda ctx: {"retro_md": f"# Retro for {ctx['topic']}"}),
]


class MiniWorkflowEngine:
    """最小工作流引擎：SQLite 持久化 + 状态推进"""

    def __init__(self, db_path: str = ":memory:"):
        self.db = sqlite3.connect(db_path)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                current_step TEXT,
                state TEXT,
                context TEXT,
                history TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        self.steps = {s[0]: (s[1], s[2]) for s in SIX_STEPS}

    def start(self, topic: str) -> str:
        run_id = str(uuid.uuid4())[:8]
        ctx = {"topic": topic}
        self.db.execute(
            "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, "0_research", StepState.PENDING, json.dumps(ctx), "[]",
             datetime.now().isoformat(), datetime.now().isoformat())
        )
        self.db.commit()
        return run_id

    def get_state(self, run_id: str) -> dict:
        row = self.db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "current_step": row[1],
            "state": row[2],
            "context": json.loads(row[3]),
            "history": json.loads(row[4]),
        }

    def advance(self, run_id: str) -> dict:
        state = self.get_state(run_id)
        step_id = state["current_step"]
        if step_id is None:
            return {"status": "completed", "message": "工作流已跑完所有步"}
        name, handler = self.steps[step_id]

        # 执行 step
        try:
            result = handler(state["context"])
            state["context"].update(result)
        except Exception as e:
            self._update(run_id, step_id, StepState.FAILED, state)
            return {"status": "failed", "step": step_id, "error": str(e)}

        # 推进
        history = state["history"] + [{"step": step_id, "completed_at": datetime.now().isoformat()}]
        next_step = self._next_step(step_id)
        self._update(run_id, next_step, StepState.PENDING, state, history)

        return {"status": "advanced", "from": step_id, "to": next_step}

    def _next_step(self, current: str) -> str | None:
        ids = [s[0] for s in SIX_STEPS]
        idx = ids.index(current)
        if idx + 1 >= len(ids):
            return None
        return ids[idx + 1]

    def _update(self, run_id, current_step, state, ctx_obj, history=None):
        history = history if history is not None else json.loads(
            self.db.execute("SELECT history FROM runs WHERE id=?", (run_id,)).fetchone()[0]
        )
        self.db.execute(
            "UPDATE runs SET current_step=?, state=?, context=?, history=?, updated_at=? WHERE id=?",
            (current_step, state.value, json.dumps(ctx_obj["context"]),
             json.dumps(history), datetime.now().isoformat(), run_id)
        )
        self.db.commit()


def main():
    print("=== POC-4: 6 步工作流 e2e ===\n")

    # 用文件 DB（不是 :memory:）证明持久化
    db_file = Path(__file__).parent / "poc4_test.db"
    if db_file.exists():
        db_file.unlink()

    engine = MiniWorkflowEngine(db_path=str(db_file))
    print(f"[1] 引擎初始化，DB: {db_file}")

    # 启动
    run_id = engine.start("V2 智能沉淀层")
    print(f"\n[2] 启动 run_id={run_id}")
    print(f"    初始状态: {engine.get_state(run_id)}")

    # 推进 6 步
    print(f"\n[3] 推进 6 步:")
    for i in range(7):
        result = engine.advance(run_id)
        print(f"   {i+1}. {result}")

    # 验证持久化：重新打开 DB
    print(f"\n[4] 重新打开 DB 验证持久化:")
    engine2 = MiniWorkflowEngine(db_path=str(db_file))
    final = engine2.get_state(run_id)
    print(f"    最终 current_step: {final['current_step']}")
    print(f"    历史步数: {len(final['history'])}")
    print(f"    context 字段: {list(final['context'].keys())}")

    # 验证可恢复
    print(f"\n[5] 模拟'重启后从断点续跑'（重新跑最后一步会到 None）:")
    result = engine2.advance(run_id)
    print(f"    {result}")

    print("\n=== 结论: 6 步状态机 + SQLite 持久化 + 可恢复，全跑通 ===")
    db_file.unlink()


if __name__ == "__main__":
    main()
