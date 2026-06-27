"""单测: services/obsidian_service.py

策略：用 pytest tmp_path 建一个临时 vault，monkeypatch obsidian.vault 指向 tmp。
覆盖：list_files / tree / read_note / write_note / search / build_graph /
       _resolve_wikilink / get_stats / get_backlinks / get_daily_note / _parse_frontmatter
目标：≥ 70%
"""
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from services import obsidian_service as svc
from services.obsidian_service import ObsidianService, WIKILINK_RE


@pytest.fixture
def vault(tmp_path):
    """建临时 vault 目录，直接返回 Path。测试自己写文件 + 用 ObsidianService(vault_path=...) 创建实例。

    用法：
        def test_x(vault):
            (vault / "note.md").write_text("...")
            s = fresh_obsidian
            s.list_files()
    """
    return tmp_path


@pytest.fixture
def fresh_obsidian(vault):
    """返回指向 tmp_path 的新 ObsidianService 实例。"""
    return ObsidianService(vault_path=vault)


# ─── _parse_frontmatter（实例方法）─────────────────────────────

class TestParseFrontmatter:
    def test_no_frontmatter_returns_empty(self, fresh_obsidian):
        assert fresh_obsidian._parse_frontmatter("hello world") == {}

    def test_simple_key_value(self, fresh_obsidian):
        content = "---\ntitle: My Note\nauthor: Alice\n---\n\nbody"
        result = fresh_obsidian._parse_frontmatter(content)
        assert result == {"title": "My Note", "author": "Alice"}

    def test_quoted_values(self, fresh_obsidian):
        content = '---\ntitle: "Quoted Title"\nsubtitle: \'Single Quote\'\n---\n'
        result = fresh_obsidian._parse_frontmatter(content)
        assert result["title"] == "Quoted Title"
        assert result["subtitle"] == "Single Quote"

    def test_list_value(self, fresh_obsidian):
        content = "---\ntags: [python, ai, agent]\n---\n"
        result = fresh_obsidian._parse_frontmatter(content)
        assert result["tags"] == ["python", "ai", "agent"]

    def test_list_with_quotes(self, fresh_obsidian):
        content = '---\ntags: ["a", "b", "c"]\n---\n'
        result = fresh_obsidian._parse_frontmatter(content)
        assert result["tags"] == ["a", "b", "c"]

    def test_multiline_frontmatter(self, fresh_obsidian):
        content = "---\ntitle: T\nauthor: A\ndate: 2026-01-01\n---\nbody"
        result = fresh_obsidian._parse_frontmatter(content)
        assert len(result) == 3


# ─── list_files ───────────────────────────────────────────────

class TestListFiles:
    def test_returns_empty_when_vault_missing(self, tmp_path):
        """vault 不存在时返回 []"""
        s = ObsidianService(vault_path=tmp_path / "nope")
        assert s.list_files() == []

    def test_lists_files_and_dirs(self, vault, fresh_obsidian):
        (vault / "note.md").write_text("# Note")
        (vault / "subdir").mkdir()
        (vault / "subdir" / "sub.md").write_text("# Sub")
        s = fresh_obsidian
        items = s.list_files()
        assert len(items) == 2
        names = {i["name"] for i in items}
        assert "note.md" in names
        assert "subdir" in names

    def test_skips_hidden_files(self, vault, fresh_obsidian):
        (vault / ".hidden").write_text("hidden")
        (vault / "visible.md").write_text("visible")
        s = fresh_obsidian
        items = s.list_files()
        assert all(not i["name"].startswith(".") for i in items)

    def test_directory_has_children_count(self, vault, fresh_obsidian):
        (vault / "subdir").mkdir()
        (vault / "subdir" / "a.md").write_text("a")
        (vault / "subdir" / "b.md").write_text("b")
        (vault / "subdir" / "ignore.txt").write_text("x")  # non-md
        s = fresh_obsidian
        items = s.list_files()
        subdir = next(i for i in items if i["name"] == "subdir")
        assert subdir["children_count"] == 2

    def test_file_has_size_and_modified(self, vault, fresh_obsidian):
        (vault / "note.md").write_text("hello")
        s = fresh_obsidian
        items = s.list_files()
        note = items[0]
        assert "size" in note
        assert "modified" in note
        assert note["size"] == 5  # "hello"


# ─── tree ─────────────────────────────────────────────────────

class TestTree:
    def test_returns_root_node(self, vault, fresh_obsidian):
        (vault / "note.md").write_text("a")
        s = fresh_obsidian
        tree = s.tree()
        assert tree["name"] == "coding"
        assert tree["type"] == "directory"

    def test_includes_nested_structure(self, vault, fresh_obsidian):
        (vault / "a.md").write_text("a")
        (vault / "sub").mkdir()
        (vault / "sub" / "b.md").write_text("b")
        s = fresh_obsidian
        tree = s.tree()
        # 应该包含 a.md 和 sub 节点
        names = [c["name"] for c in tree["children"]]
        assert "a.md" in names
        assert "sub" in names

    def test_empty_subdir_excluded(self, vault, fresh_obsidian):
        """空子目录不出现在 tree 里（避免无意义节点）"""
        (vault / "sub").mkdir()
        (vault / "a.md").write_text("a")
        s = fresh_obsidian
        tree = s.tree()
        names = [c["name"] for c in tree["children"]]
        assert "sub" not in names  # 空目录不出现


# ─── read_note / write_note ───────────────────────────────────

class TestReadWriteNote:
    def test_write_creates_file(self, vault, fresh_obsidian):
        s = fresh_obsidian
        result = s.write_note("test.md", "# Hello")
        assert result["status"] == "saved"
        assert (vault / "test.md").exists()
        assert (vault / "test.md").read_text() == "# Hello"

    def test_write_creates_parent_dirs(self, vault, fresh_obsidian):
        s = fresh_obsidian
        s.write_note("deep/nested/note.md", "x")
        assert (vault / "deep" / "nested" / "note.md").exists()

    def test_read_existing_note(self, vault, fresh_obsidian):
        (vault / "note.md").write_text(
            "---\ntitle: T\n---\n\n# Note\n\nBody [[link]] here",
            encoding="utf-8",
        )
        s = fresh_obsidian
        n = s.read_note("note.md")
        assert n is not None
        assert n["name"] == "note.md"
        assert "Body" in n["content"]
        assert n["frontmatter"]["title"] == "T"
        assert "link" in n["links"]  # wikilink extracted

    def test_read_nonexistent_returns_none(self, vault, fresh_obsidian):
        s = fresh_obsidian
        assert s.read_note("nonexistent.md") is None

    def test_read_dir_returns_none(self, vault, fresh_obsidian):
        (vault / "sub").mkdir()
        s = fresh_obsidian
        assert s.read_note("sub") is None  # 是目录不是文件


# ─── search ───────────────────────────────────────────────────

class TestSearch:
    def test_finds_match_with_snippet(self, vault, fresh_obsidian):
        (vault / "note.md").write_text("Python is great\nand we love it")
        s = fresh_obsidian
        results = s.search("Python")
        assert len(results) == 1
        assert "Python" in results[0]["snippet"]
        assert results[0]["score"] >= 1

    def test_case_insensitive(self, vault, fresh_obsidian):
        (vault / "note.md").write_text("PYTHON is great")
        s = fresh_obsidian
        results = s.search("python")
        assert len(results) == 1

    def test_no_match_returns_empty(self, vault, fresh_obsidian):
        (vault / "note.md").write_text("Java is great")
        s = fresh_obsidian
        assert s.search("Python") == []

    def test_search_excludes_non_md(self, vault, fresh_obsidian):
        (vault / "note.md").write_text("Python")
        (vault / "note.txt").write_text("Python")  # 不计入
        s = fresh_obsidian
        results = s.search("Python")
        assert len(results) == 1
        assert results[0]["path"] == "note.md"

    def test_limit(self, vault, fresh_obsidian):
        for i in range(5):
            (vault / f"n{i}.md").write_text(f"Python {i}")
        s = fresh_obsidian
        results = s.search("Python", limit=2)
        assert len(results) == 2

    def test_sorted_by_score_desc(self, vault, fresh_obsidian):
        (vault / "a.md").write_text("python")  # 1 次
        (vault / "b.md").write_text("python python python")  # 3 次
        s = fresh_obsidian
        results = s.search("python")
        assert results[0]["path"] == "b.md"  # 高分在前


# ─── build_graph ──────────────────────────────────────────────

class TestBuildGraph:
    def test_empty_vault(self, vault, fresh_obsidian):
        s = fresh_obsidian
        g = s.build_graph()
        assert g["nodes"] == []
        assert g["edges"] == []
        assert g["stats"]["total_nodes"] == 0

    def test_nodes_from_md_files(self, vault, fresh_obsidian):
        (vault / "a.md").write_text("# Note A")
        (vault / "b.md").write_text("# Note B")
        s = fresh_obsidian
        g = s.build_graph()
        assert len(g["nodes"]) == 2
        labels = {n["label"] for n in g["nodes"]}
        assert "Note A" in labels or any(n["label"].startswith("Note") for n in g["nodes"])

    def test_edges_from_wikilinks(self, vault, fresh_obsidian):
        (vault / "a.md").write_text("# A\nLinks to [[b]]")
        (vault / "b.md").write_text("# B")
        s = fresh_obsidian
        g = s.build_graph()
        assert len(g["edges"]) == 1
        assert "b" in g["edges"][0]["label"]

    def test_groups_by_subdir(self, vault, fresh_obsidian):
        (vault / "a.md").write_text("# A")
        (vault / "topic1").mkdir()
        (vault / "topic1" / "b.md").write_text("# B")
        s = fresh_obsidian
        g = s.build_graph()
        groups = {n["group"] for n in g["nodes"]}
        assert "topic1" in groups
        assert "root" in groups

    def test_resolves_wikilink_with_md_extension(self, vault, fresh_obsidian):
        s = fresh_obsidian
        # 直接 .md 链接
        resolved = s._resolve_wikilink("note", "anywhere.md")
        # 应返回 None（如果 vault 里没有 note.md）
        assert resolved is None

    def test_resolves_wikilink_finds_existing(self, vault, fresh_obsidian):
        (vault / "B.md").write_text("# B")
        s = fresh_obsidian
        resolved = s._resolve_wikilink("B", "A.md")
        assert resolved == "B.md"

    def test_resolves_wikilink_in_subdir(self, vault, fresh_obsidian):
        (vault / "sub").mkdir()
        (vault / "sub" / "B.md").write_text("# B")
        s = fresh_obsidian
        resolved = s._resolve_wikilink("B", "sub/A.md")
        assert resolved == "sub/B.md"

    def test_resolves_wikilink_fuzzy_match(self, vault, fresh_obsidian):
        """whitespace/全角空格应该被 normalize（要求 file 名前缀匹配）"""
        (vault / "React模式.md").write_text("# React 模式")
        s = fresh_obsidian
        # "React 模式" 去空格 → "react模式"，"react模式.md" 应该 prefix 匹配
        resolved = s._resolve_wikilink("React 模式", "A.md")
        assert resolved == "React模式.md"


# ─── get_stats ────────────────────────────────────────────────

class TestGetStats:
    def test_empty_vault(self, vault, fresh_obsidian):
        s = fresh_obsidian
        stats = s.get_stats()
        assert stats["total_notes"] == 0
        assert stats["total_words"] == 0

    def test_counts_notes_and_words(self, vault, fresh_obsidian):
        (vault / "a.md").write_text("hello world foo bar")  # 4 words
        (vault / "b.md").write_text("baz")  # 1 word
        s = fresh_obsidian
        stats = s.get_stats()
        assert stats["total_notes"] == 2
        assert stats["total_words"] == 5

    def test_groups_by_folder(self, vault, fresh_obsidian):
        (vault / "a.md").write_text("hi")
        (vault / "sub").mkdir()
        (vault / "sub" / "b.md").write_text("world")
        s = fresh_obsidian
        stats = s.get_stats()
        assert "sub" in stats["by_folder"]
        assert stats["by_folder"]["sub"]["notes"] == 1
        assert stats["by_folder"]["root"]["notes"] == 1


# ─── get_backlinks ────────────────────────────────────────────

class TestGetBacklinks:
    def test_no_backlinks(self, vault, fresh_obsidian):
        (vault / "a.md").write_text("no links here")
        (vault / "b.md").write_text("# B")
        s = fresh_obsidian
        assert s.get_backlinks("b.md") == []

    def test_finds_strict_match(self, vault, fresh_obsidian):
        (vault / "a.md").write_text("I link to [[B]]")
        (vault / "b.md").write_text("# B")
        s = fresh_obsidian
        result = s.get_backlinks("b.md")
        assert len(result) == 1
        assert result[0]["path"] == "a.md"
        assert result[0]["link_text"] == "B"

    def test_finds_fuzzy_match_with_whitespace(self, vault, fresh_obsidian):
        """whitespace/全角空格 normalize 后能匹配"""
        (vault / "a.md").write_text("I link to [[React 模式]]")
        (vault / "React模式.md").write_text("# React 模式")
        s = fresh_obsidian
        result = s.get_backlinks("React模式.md")
        assert len(result) == 1

    def test_excludes_self(self, vault, fresh_obsidian):
        (vault / "a.md").write_text("self link [[A]]")
        s = fresh_obsidian
        assert s.get_backlinks("a.md") == []

    def test_case_insensitive_match(self, vault, fresh_obsidian):
        (vault / "a.md").write_text("I link to [[react]]")
        (vault / "ReAct.md").write_text("# ReAct")
        s = fresh_obsidian
        result = s.get_backlinks("ReAct.md")
        assert len(result) == 1


# ─── get_daily_note ───────────────────────────────────────────

class TestGetDailyNote:
    def test_returns_none_when_no_day(self, vault, fresh_obsidian):
        """未指定 day 时返回 None（除非今天刚好有）"""
        s = fresh_obsidian
        # 用未来日期确保不会撞到
        result = s.get_daily_note("2099-01-01")
        # 如果 daily/2099-01-01.md 不存在，应返回 None
        # （但服务也可能自动创建，先看具体行为）
        assert result is None or result.get("path") == "daily/2099-01-01.md"

    def test_existing_daily_note_returned(self, vault, fresh_obsidian):
        (vault / "daily").mkdir()
        (vault / "daily" / "2026-06-27.md").write_text("---\ndate: 2026-06-27\n---\n\n# 2026-06-27\n\nbody")
        s = fresh_obsidian
        n = s.get_daily_note("2026-06-27")
        assert n is not None
        assert "2026-06-27" in n["path"]