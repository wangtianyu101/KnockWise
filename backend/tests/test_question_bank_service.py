"""单测: services/question_bank_service.py

覆盖 17 个函数 / helper，覆盖率目标 ≥ 80%。
策略：mock_db + mock_cache（已 in conftest.py），不接真 DB。
"""
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timezone

import pytest

from services import question_bank_service as svc


# ─── 工具函数（pure）─────────────────────────────────────────

class TestFilterCacheKey:
    def test_deterministic_same_input(self):
        a = svc._filter_cache_key("u-1", {"topic": "agent"}, 1, 20)
        b = svc._filter_cache_key("u-1", {"topic": "agent"}, 1, 20)
        assert a == b

    def test_different_user_different_key(self):
        a = svc._filter_cache_key("u-1", {}, 1, 20)
        b = svc._filter_cache_key("u-2", {}, 1, 20)
        assert a != b

    def test_different_filter_different_key(self):
        a = svc._filter_cache_key("u-1", {"topic": "agent"}, 1, 20)
        b = svc._filter_cache_key("u-1", {"topic": "rag"}, 1, 20)
        assert a != b

    def test_key_format(self):
        k = svc._filter_cache_key("u", {}, 1, 20)
        assert k.startswith("question_list:")
        assert len(k.split(":")[1]) == 16  # md5 截 16 字符


class TestSeedToItem:
    def test_basic_fields(self):
        q = MagicMock()
        q.id = "q-1"
        q.topic = "agent"
        q.sub_topic = "react"
        q.difficulty = 3
        q.question_text = "什么是 ReAct？"
        item = svc._seed_to_item(q, None)
        assert item["id"] == "q-1"
        assert item["source"] == "seed"
        assert item["progress"] is None

    def test_with_progress(self):
        q = MagicMock(id="q-1", topic="agent", sub_topic=None, difficulty=3, question_text="Q?")
        p = MagicMock(id="p-1", status="mastered", practice_count=5, correct_count=4,
                      bookmarked=True, ease_factor=2.5, interval_days=10,
                      next_review_at=None, last_practiced_at=None)
        item = svc._seed_to_item(q, p)
        assert item["progress"]["status"] == "mastered"
        assert item["progress"]["bookmarked"] is True


class TestUserQuestionToItem:
    def test_handles_none_topic(self):
        u = MagicMock(id="u-1", topic=None, sub_topic=None, difficulty=2,
                      question_text="text", source="user_note")
        item = svc._user_question_to_item(u, None)
        assert item["topic"] == ""
        assert item["sub_topic"] == ""
        assert item["source"] == "user_note"

    def test_with_progress(self):
        u = MagicMock(id="u-1", topic="agent", sub_topic="react", difficulty=2,
                      question_text="t", source="interview")
        p = MagicMock(id="p-1", status="learning", practice_count=1, correct_count=1,
                      bookmarked=False, ease_factor=2.5, interval_days=1,
                      next_review_at=None, last_practiced_at=None)
        item = svc._user_question_to_item(u, p)
        assert item["progress"]["practice_count"] == 1


class TestProgressToDict:
    def test_datetime_serialized_to_iso(self):
        dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        p = MagicMock(id="p-1", status="learning", practice_count=2, correct_count=2,
                      bookmarked=False, ease_factor=2.5, interval_days=5,
                      next_review_at=dt, last_practiced_at=dt)
        d = svc._progress_to_dict(p)
        assert d["next_review_at"] == "2026-01-01T12:00:00+00:00"

    def test_none_datetime_becomes_none_string(self):
        p = MagicMock(id="p-1", status="new", practice_count=0, correct_count=0,
                      bookmarked=False, ease_factor=2.5, interval_days=0,
                      next_review_at=None, last_practiced_at=None)
        d = svc._progress_to_dict(p)
        assert d["next_review_at"] is None


class TestSortItems:
    def test_sort_by_difficulty_desc(self):
        items = [{"id": "a", "difficulty": 2}, {"id": "b", "difficulty": 5}, {"id": "c", "difficulty": 3}]
        sorted_items = svc._sort_items(items, "difficulty")
        assert [i["id"] for i in sorted_items] == ["b", "c", "a"]

    def test_sort_by_id_default(self):
        items = [{"id": "c"}, {"id": "a"}, {"id": "b"}]
        sorted_items = svc._sort_items(items, "id")
        assert [i["id"] for i in sorted_items] == ["a", "b", "c"]

    def test_sort_by_last_practiced(self):
        items = [
            {"id": "a", "progress": {"last_practiced_at": "2026-01-02"}},
            {"id": "b", "progress": None},
            {"id": "c", "progress": {"last_practiced_at": "2026-01-03"}},
        ]
        sorted_items = svc._sort_items(items, "last_practiced")
        # c > a > b (None 当 "")
        assert sorted_items[0]["id"] == "c"

    def test_sort_random_returns_same_count(self):
        items = [{"id": str(i)} for i in range(10)]
        sorted_items = svc._sort_items(items, "random")
        assert len(sorted_items) == 10

    def test_sort_handles_none_difficulty(self):
        items = [{"id": "a", "difficulty": None}, {"id": "b", "difficulty": 3}]
        sorted_items = svc._sort_items(items, "difficulty")
        assert sorted_items[0]["id"] == "b"  # None 当 0


# ─── list_questions（DB + cache）─────────────────────────────

class TestListQuestions:
    async def test_returns_cached_value_when_cache_hit(self, mock_db, mock_cache):
        cached = {"items": [], "total": 0, "page": 1, "size": 20}
        mock_cache.get = AsyncMock(return_value=cached)

        result = await svc.list_questions(mock_db, "u-1")
        assert result == cached
        mock_db.execute.assert_not_called()

    async def test_db_query_when_cache_miss(self, mock_db, mock_cache):
        mock_cache.get = AsyncMock(return_value=None)
        from tests.conftest import FakeResult
        # progress query、seed query、user query 都返回空
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[]))

        result = await svc.list_questions(mock_db, "u-1", topic="agent")
        assert result["items"] == []
        assert result["total"] == 0
        # 至少被调 3 次：progress、seed、user
        assert mock_db.execute.await_count >= 3
        # 写入 cache
        mock_cache.set.assert_awaited_once()

    async def test_bookmarked_true_filters_unbookmarked(self, mock_db, mock_cache):
        mock_cache.get = AsyncMock(return_value=None)
        from tests.conftest import FakeResult

        # Mock seed question
        seed_q = MagicMock(id="q-1", topic="agent", sub_topic="react", difficulty=3,
                           question_text="Q?")
        progress = MagicMock(id="p-1", status="mastered", practice_count=5, correct_count=5,
                             bookmarked=False, ease_factor=2.5, interval_days=10,
                             next_review_at=None, last_practiced_at=None)

        # 第一次 execute = progress query，第二次 = seed，第三次 = user
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[progress]),  # progress
            FakeResult(items=[seed_q]),     # seed
            FakeResult(items=[]),           # user
        ])

        result = await svc.list_questions(mock_db, "u-1", bookmarked=True)
        # 因为 progress.bookmarked=False，seed 题被过滤
        assert result["items"] == []

    async def test_text_search_filter(self, mock_db, mock_cache):
        """q 参数触发 question_text.contains()"""
        mock_cache.get = AsyncMock(return_value=None)
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[]), FakeResult(items=[]), FakeResult(items=[]),
        ])
        await svc.list_questions(mock_db, "u-1", q="ReAct")
        # 至少调 3 次（progress + seed with q + user with q）
        assert mock_db.execute.await_count >= 3

    async def test_bookmarked_true_for_user_question_filters(self, mock_db, mock_cache):
        """bookmarked=True 时 user_question 没 progress 或没 bookmark 就过滤"""
        mock_cache.get = AsyncMock(return_value=None)
        from tests.conftest import FakeResult

        seed_q = MagicMock(id="q-1", topic="agent", sub_topic="react", difficulty=3, question_text="Q?")
        user_q = MagicMock(id="12345678-1234-1234-1234-123456789012",
                            topic="agent", sub_topic=None, difficulty=3,
                            question_text="User Q?", source="user_note")
        # user_q 没 progress，所以被过滤
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[]),  # progress 空
            FakeResult(items=[seed_q]),  # seed 有 1 题，但没 progress，bookmark=True 也过滤
            FakeResult(items=[user_q]),  # user 有 1 题，没 progress，被过滤
        ])

        result = await svc.list_questions(mock_db, "u-1", bookmarked=True)
        assert result["items"] == []

    async def test_pagination(self, mock_db, mock_cache):
        mock_cache.get = AsyncMock(return_value=None)
        from tests.conftest import FakeResult

        seed_qs = [
            MagicMock(id=f"q-{i}", topic="agent", sub_topic="x", difficulty=3,
                      question_text=f"Q{i}?") for i in range(5)
        ]
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[]),            # progress
            FakeResult(items=seed_qs),       # seed
            FakeResult(items=[]),            # user
        ])

        result = await svc.list_questions(mock_db, "u-1", page=2, size=2)
        assert result["page"] == 2
        assert result["size"] == 2
        assert len(result["items"]) == 2  # 5 题，第 2 页 2 条
        assert result["total"] == 5


# ─── get_question_detail ──────────────────────────────────────

class TestGetQuestionDetail:
    async def test_returns_none_when_not_found(self, mock_db):
        mock_db.get = AsyncMock(return_value=None)
        result = await svc.get_question_detail(mock_db, "u-1", "q-not-exist")
        assert result is None

    async def test_returns_seed_question_detail(self, mock_db):
        seed_q = MagicMock(id="q-1", topic="agent", sub_topic="react", difficulty=3,
                           question_text="什么是 ReAct？",
                           answer_key_points=["point1", "point2"],
                           followup_tree={"type": "tree"})
        mock_db.get = AsyncMock(side_effect=[seed_q, None])
        # 让 progress query 返回空（tag / progress / note）
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[], scalar=None))

        result = await svc.get_question_detail(mock_db, "u-1", "q-1")
        assert result["id"] == "q-1"
        assert result["source"] == "seed"
        assert result["answer_key_points"] == ["point1", "point2"]

    async def test_returns_user_question_detail(self, mock_db):
        u_qid = "12345678-1234-1234-1234-123456789012"  # 36 chars UUID
        u_q = MagicMock(id=u_qid, topic="custom", sub_topic="custom2", difficulty=2,
                        question_text="My question", answer="my answer", source="user_note",
                        user_id="u-1", tags=["tag1"])
        mock_db.get = AsyncMock(side_effect=[None, u_q])  # seed miss, user hit
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=None, items=[]))

        result = await svc.get_question_detail(mock_db, "u-1", u_qid)
        assert result["source"] == "user_note"
        assert result["answer_key_points"] == ["my answer"]
        assert result["tags"] == ["tag1"]

    async def test_user_question_wrong_owner_returns_none(self, mock_db):
        u_qid = "12345678-1234-1234-1234-123456789012"
        u_q = MagicMock(id=u_qid, user_id="OTHER-USER")
        mock_db.get = AsyncMock(side_effect=[None, u_q])
        result = await svc.get_question_detail(mock_db, "u-1", u_qid)
        assert result is None


# ─── UserQuestion CRUD ────────────────────────────────────────

class TestCreateUserQuestion:
    async def test_creates_with_defaults(self, mock_db, mock_cache):
        data = {"question_text": "test?"}
        result = await svc.create_user_question(mock_db, "u-1", data)
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited()
        mock_cache.delete_pattern.assert_awaited()

    async def test_creates_with_all_fields(self, mock_db, mock_cache):
        data = {
            "question_text": "test?",
            "answer": "my answer",
            "topic": "agent",
            "sub_topic": "react",
            "difficulty": 5,
            "tags": ["a"],
            "source": "interview",
        }
        await svc.create_user_question(mock_db, "u-1", data)
        added = mock_db.add.call_args.args[0]
        assert added.question_text == "test?"
        assert added.difficulty == 5
        assert added.source == "interview"


class TestUpdateUserQuestion:
    async def test_returns_none_when_not_found(self, mock_db, mock_cache):
        mock_db.get = AsyncMock(return_value=None)
        result = await svc.update_user_question(mock_db, "u-1", "q-1", {"topic": "new"})
        assert result is None

    async def test_returns_none_when_owner_mismatch(self, mock_db, mock_cache):
        uq = MagicMock(user_id="OTHER")
        mock_db.get = AsyncMock(return_value=uq)
        result = await svc.update_user_question(mock_db, "u-1", "q-1", {})
        assert result is None

    async def test_updates_specified_fields(self, mock_db, mock_cache):
        uq = MagicMock(user_id="u-1", question_text="old", topic="old", difficulty=2)
        mock_db.get = AsyncMock(return_value=uq)
        await svc.update_user_question(mock_db, "u-1", "q-1", {"topic": "new", "difficulty": 5})
        assert uq.topic == "new"
        assert uq.difficulty == 5
        # 没传的字段不动
        assert uq.question_text == "old"
        mock_cache.delete_pattern.assert_awaited()


class TestDeleteUserQuestion:
    async def test_returns_false_when_not_found(self, mock_db, mock_cache):
        mock_db.get = AsyncMock(return_value=None)
        assert await svc.delete_user_question(mock_db, "u-1", "q-1") is False

    async def test_returns_false_when_owner_mismatch(self, mock_db, mock_cache):
        uq = MagicMock(user_id="OTHER")
        mock_db.get = AsyncMock(return_value=uq)
        assert await svc.delete_user_question(mock_db, "u-1", "q-1") is False

    async def test_deletes_and_invalidates_cache(self, mock_db, mock_cache):
        uq = MagicMock(user_id="u-1")
        mock_db.get = AsyncMock(return_value=uq)
        result = await svc.delete_user_question(mock_db, "u-1", "q-1")
        assert result is True
        mock_db.delete.assert_awaited_with(uq)
        mock_db.commit.assert_awaited()
        mock_cache.delete_pattern.assert_awaited()


class TestInvalidateUserListCache:
    async def test_calls_delete_pattern(self, mock_cache):
        await svc._invalidate_user_list_cache("u-1")
        mock_cache.delete_pattern.assert_awaited_with("question_list:*")


# ─── Tag 管理 ────────────────────────────────────────────────

class TestListTags:
    async def test_returns_list_of_dicts(self, mock_db):
        from tests.conftest import FakeResult
        from types import SimpleNamespace
        t1 = SimpleNamespace(id="t-1", name="agent", color="#fff", is_system=True, user_id=None)
        t2 = SimpleNamespace(id="t-2", name="custom", color="#000", is_system=False, user_id="u-1")
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[t1, t2]))

        result = await svc.list_tags(mock_db, "u-1")
        assert len(result) == 2
        assert result[0]["name"] == "agent"
        assert result[1]["name"] == "custom"

    async def test_no_user_id_returns_only_system(self, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[]))
        await svc.list_tags(mock_db)
        mock_db.execute.assert_awaited()

    async def test_include_system_false_filters(self, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[]))
        await svc.list_tags(mock_db, "u-1", include_system=False)
        mock_db.execute.assert_awaited()


class TestCreateTag:
    async def test_user_tag(self, mock_db):
        await svc.create_tag(mock_db, "u-1", "my-tag", color="#abc")
        added = mock_db.add.call_args.args[0]
        assert added.name == "my-tag"
        assert added.user_id == "u-1"
        assert added.is_system is False

    async def test_system_tag_has_no_user(self, mock_db):
        await svc.create_tag(mock_db, "u-1", "sys", is_system=True)
        added = mock_db.add.call_args.args[0]
        assert added.user_id is None
        assert added.is_system is True


class TestAddTagToQuestion:
    async def test_idempotent_when_already_exists(self, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar="existing"))
        result = await svc.add_tag_to_question(mock_db, "q-1", "t-1")
        assert result is True
        # 不应该 add
        mock_db.add.assert_not_called()

    async def test_adds_new_tag_map(self, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=None))
        result = await svc.add_tag_to_question(mock_db, "q-1", "t-1")
        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited()


class TestRemoveTagFromQuestion:
    async def test_returns_false_when_not_found(self, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=None))
        assert await svc.remove_tag_from_question(mock_db, "q-1", "t-1") is False

    async def test_removes_existing(self, mock_db):
        m = MagicMock()
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=m))
        result = await svc.remove_tag_from_question(mock_db, "q-1", "t-1")
        assert result is True
        mock_db.delete.assert_awaited_with(m)
        mock_db.commit.assert_awaited()


class TestGetTagsForQuestion:
    async def test_returns_tag_names(self, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(items=["agent", "rag"]))
        tags = await svc._get_tags_for_question(mock_db, "q-1")
        assert tags == ["agent", "rag"]


# ─── User Note ────────────────────────────────────────────────

class TestGetUserNote:
    async def test_returns_none_when_not_found(self, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=None))
        assert await svc.get_user_note(mock_db, "u-1", "q-1") is None

    async def test_returns_note_dict(self, mock_db):
        n = MagicMock(id="n-1", content_md="# My note",
                      updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=n))
        result = await svc.get_user_note(mock_db, "u-1", "q-1")
        assert result["content_md"] == "# My note"
        assert result["updated_at"] is not None


class TestUpsertUserNote:
    async def test_create_new_note(self, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=None))  # 不存在
        result = await svc.upsert_user_note(mock_db, "u-1", "q-1", "# new note")
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited()

    async def test_update_existing_note(self, mock_db):
        existing = MagicMock(content_md="old", updated_at=None)
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=existing))
        await svc.upsert_user_note(mock_db, "u-1", "q-1", "new content")
        # 不 add，只改 content_md
        mock_db.add.assert_not_called()
        assert existing.content_md == "new content"


class TestGetUserNoteHelper:
    async def test_delegates_to_get_user_note(self, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=None))
        result = await svc._get_user_note(mock_db, "u-1", "q-1")
        assert result is None