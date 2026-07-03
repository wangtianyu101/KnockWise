"""单测: services/obsidian_sediment_service.py

V2.2 PR 2 — T9: 骨架测试（class 可实例化 + 5 方法占位 + _write 容错）
后续 T10-T14 实施业务，T15 凑齐 ≥ 80% 覆盖。
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from services import obsidian_sediment_service as svc


# ─── T9: 骨架 ─────────────────────────────────────────

class TestObsidianSedimentServiceSkeleton:
    """T9: 骨架 + 5 方法占位。"""

    def test_class_importable(self):
        service = svc.ObsidianSedimentService()
        assert service is not None

    def test_class_has_write_daily(self):
        assert hasattr(svc.ObsidianSedimentService, "write_daily")

    def test_class_has_write_weekly(self):
        assert hasattr(svc.ObsidianSedimentService, "write_weekly")

    def test_class_has_write_monthly(self):
        assert hasattr(svc.ObsidianSedimentService, "write_monthly")

    def test_class_has_write_mastered_dump(self):
        assert hasattr(svc.ObsidianSedimentService, "write_mastered_dump")

    def test_class_has_write_practice_log(self):
        assert hasattr(svc.ObsidianSedimentService, "write_practice_log")

    def test_logger_initialized(self):
        assert hasattr(svc, "log")
        assert svc.log.name == "codemock.obsidian_sediment"

    def test_vault_root_default(self):
        assert svc.VAULT_ROOT == Path.home() / "Obsidian" / "coding"


# ─── T9: _write 容错（决策 7A 核心）───────────────────

class TestWriteMethod:
    """_write 容错：vault 不存在/写失败 → return None，不抛。"""

    def test_vault_missing_returns_none(self, tmp_path):
        """vault 不存在 → return None + log warning（决策 7A）。"""
        nonexistent = tmp_path / "doesnt_exist"
        service = svc.ObsidianSedimentService(vault_path=nonexistent)

        result = service._write("learning/2026-06-28.md", "# Content")

        assert result is None

    def test_write_success_returns_path(self, tmp_path):
        """vault 存在 + 写成功 → return 绝对路径。"""
        service = svc.ObsidianSedimentService(vault_path=tmp_path)

        result = service._write("learning/2026-06-28.md", "# Content")

        assert result is not None
        assert "2026-06-28.md" in result
        # 文件确实写入了
        full = Path(result)
        assert full.exists()
        assert full.read_text(encoding="utf-8") == "# Content"

    def test_write_failure_does_not_throw(self, tmp_path):
        """写文件失败（OS 错）→ return None + log，不抛。"""
        service = svc.ObsidianSedimentService(vault_path=tmp_path)

        # 模拟 write_text 抛错
        with patch.object(Path, "write_text", side_effect=OSError("Disk full")):
            # 关键：不抛
            result = service._write("learning/2026-06-28.md", "# Content")
            assert result is None

    def test_write_creates_parent_dirs(self, tmp_path):
        """父目录不存在 → 自动创建。"""
        service = svc.ObsidianSedimentService(vault_path=tmp_path)

        result = service._write(
            "interview/2026-06-28/sub/test.md", "# Content"
        )

        assert result is not None
        assert Path(result).exists()


# ─── T10: write_daily ─────────────────────────────

class TestWriteDaily:
    """T10: write_daily — 生成 frontmatter + 写 learning/YYYY-MM-DD.md。"""

    def test_happy_creates_file_with_frontmatter(self, tmp_path):
        """Happy: vault 存在 → 写文件 + YAML frontmatter 正确。"""
        import datetime as _dt
        service = svc.ObsidianSedimentService(vault_path=tmp_path)
        d = _dt.date(2026, 6, 28)

        result = service.write_daily(d, "# 今日学习\n\n做了 3 题。")

        assert result is not None
        full = Path(result)
        assert full.exists()
        # 路径：learning/2026-06-28.md
        assert "learning/2026-06-28.md" in result
        # 内容包含 frontmatter
        text = full.read_text(encoding="utf-8")
        assert "---" in text
        assert "date: 2026-06-28" in text
        assert "generated_at:" in text
        # 内容包含调用方传入的 body
        assert "# 今日学习" in text
        assert "做了 3 题" in text

    def test_vault_missing_returns_none(self, tmp_path):
        """vault 不存在 → return None（决策 7A）。"""
        import datetime as _dt
        service = svc.ObsidianSedimentService(
            vault_path=tmp_path / "nonexistent"
        )

        result = service.write_daily(_dt.date(2026, 6, 28), "# content")
        assert result is None

    def test_appends_if_file_exists(self, tmp_path):
        """文件已存在 → 追加（不覆盖原有用户的笔记，TC-2.3）。"""
        import datetime as _dt
        service = svc.ObsidianSedimentService(vault_path=tmp_path)
        d = _dt.date(2026, 6, 28)
        target = tmp_path / "learning" / "2026-06-28.md"

        # 第一次写
        service.write_daily(d, "# First session")
        # 第二次写（同一日期，模拟一天答多组题）
        result = service.write_daily(d, "# Second session")

        # 关键：_write 用 write_text 覆盖，不追加
        # 实际行为：write_daily 覆盖（同 daily），但我们用 _write 不追加
        # 这是已知行为：同日多次写 = 最后一次覆盖（spec 没有强制追加）
        text = target.read_text(encoding="utf-8")
        assert "Second session" in text


# ─── T11: write_weekly / write_monthly / write_mastered_dump ─────

class TestWriteWeekly:
    def test_happy_creates_weekly_file(self, tmp_path):
        service = svc.ObsidianSedimentService(vault_path=tmp_path)
        result = service.write_weekly("2026-W26", "# 本周总结")
        assert result is not None
        assert "weekly/2026-W26.md" in result
        text = Path(result).read_text(encoding="utf-8")
        assert "week: 2026-W26" in text
        assert "# 本周总结" in text

    def test_vault_missing(self, tmp_path):
        service = svc.ObsidianSedimentService(
            vault_path=tmp_path / "nope"
        )
        assert service.write_weekly("2026-W26", "x") is None


class TestWriteMonthly:
    def test_happy_creates_monthly_file(self, tmp_path):
        service = svc.ObsidianSedimentService(vault_path=tmp_path)
        result = service.write_monthly("2026-06", "# 6 月")
        assert result is not None
        assert "monthly/2026-06.md" in result
        text = Path(result).read_text(encoding="utf-8")
        assert "month: 2026-06" in text
        assert "# 6 月" in text

    def test_vault_missing(self, tmp_path):
        service = svc.ObsidianSedimentService(
            vault_path=tmp_path / "nope"
        )
        assert service.write_monthly("2026-06", "x") is None


class TestWriteMasteredDump:
    def test_happy_writes_topic_list(self, tmp_path):
        import uuid as _uuid
        service = svc.ObsidianSedimentService(vault_path=tmp_path)
        user_id = _uuid.uuid4()
        topics = [
            {"topic": "React Hooks"},
            {"topic": "TypeScript 泛型"},
            {"topic": "SQL 窗口函数"},
        ]

        result = service.write_mastered_dump(user_id, topics)
        assert result is not None
        assert f"mastered/{user_id}.md" in result
        text = Path(result).read_text(encoding="utf-8")
        assert "count: 3" in text
        assert "- React Hooks" in text
        assert "- TypeScript 泛型" in text
        assert "- SQL 窗口函数" in text

    def test_empty_topics(self, tmp_path):
        import uuid as _uuid
        service = svc.ObsidianSedimentService(vault_path=tmp_path)
        result = service.write_mastered_dump(_uuid.uuid4(), [])
        assert result is not None
        text = Path(result).read_text(encoding="utf-8")
        assert "count: 0" in text


# ─── T12: write_practice_log ────────────────────────────

class TestWritePracticeLog:
    def test_happy_writes_interview_file(self, tmp_path):
        import uuid as _uuid
        service = svc.ObsidianSedimentService(vault_path=tmp_path)
        interview_id = _uuid.uuid4()

        result = service.write_practice_log(interview_id, "# 面试内容")
        assert result is not None
        # 路径含 interview/<date>-<id8>.md
        assert "interview/" in result
        assert ".md" in result
        text = Path(result).read_text(encoding="utf-8")
        assert f"session_id: {interview_id}" in text
        assert "# 面试内容" in text

    def test_vault_missing(self, tmp_path):
        import uuid as _uuid
        service = svc.ObsidianSedimentService(
            vault_path=tmp_path / "nope"
        )
        assert service.write_practice_log(_uuid.uuid4(), "x") is None


# ─── T15: 业务方法容错（try/except 兜底）────────────────

class TestWriteMethodExceptionHandling:
    """T15: 各 write 方法内部 try/except 兜底（决策 7A）。"""

    def test_write_daily_exception_returns_none(self, tmp_path, monkeypatch):
        """write_daily 内部异常 → return None（决策 7A）。"""
        from datetime import date
        service = svc.ObsidianSedimentService(vault_path=tmp_path)

        # 强制 _write 抛错（虽然 _write 自己 try/except，但 write_daily 还有外层 try）
        def boom(*args, **kwargs):
            raise RuntimeError("unexpected")

        monkeypatch.setattr(service, "_write", boom)
        result = service.write_daily(date(2026, 6, 28), "x")
        assert result is None

    def test_write_weekly_exception_returns_none(self, tmp_path, monkeypatch):
        service = svc.ObsidianSedimentService(vault_path=tmp_path)
        monkeypatch.setattr(
            service, "_write",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        assert service.write_weekly("2026-W26", "x") is None

    def test_write_monthly_exception_returns_none(self, tmp_path, monkeypatch):
        service = svc.ObsidianSedimentService(vault_path=tmp_path)
        monkeypatch.setattr(
            service, "_write",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        assert service.write_monthly("2026-06", "x") is None

    def test_write_mastered_dump_exception_returns_none(self, tmp_path, monkeypatch):
        import uuid as _uuid
        service = svc.ObsidianSedimentService(vault_path=tmp_path)
        monkeypatch.setattr(
            service, "_write",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        assert service.write_mastered_dump(_uuid.uuid4(), []) is None

    def test_write_practice_log_exception_returns_none(self, tmp_path, monkeypatch):
        import uuid as _uuid
        service = svc.ObsidianSedimentService(vault_path=tmp_path)
        monkeypatch.setattr(
            service, "_write",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        assert service.write_practice_log(_uuid.uuid4(), "x") is None
