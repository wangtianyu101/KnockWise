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
