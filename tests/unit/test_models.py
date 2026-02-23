"""Pydantic モデルのバリデーションテスト"""

import pytest
from pydantic import ValidationError

from domain.models import (
    ChatMessage,
    DocumentChunk,
    JudgeResult,
    MessageRole,
    SearchResult,
    Subtask,
    TaskPlanningResult,
)


# ---------------------------------------------------------------------------
# ChatMessage
# ---------------------------------------------------------------------------


class TestChatMessage:
    """ChatMessage のテスト"""

    def test_create_user_message(self) -> None:
        """ユーザーメッセージを作成できることを検証する。"""
        msg = ChatMessage(role=MessageRole.USER, content="テスト質問")
        assert msg.role == MessageRole.USER
        assert msg.content == "テスト質問"

    def test_frozen(self) -> None:
        """frozen=True により属性変更が禁止されることを検証する。"""
        msg = ChatMessage(role=MessageRole.USER, content="テスト")
        with pytest.raises(ValidationError):
            msg.content = "変更"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# DocumentChunk
# ---------------------------------------------------------------------------


class TestDocumentChunk:
    """DocumentChunk のテスト"""

    def test_create_chunk(self) -> None:
        """チャンクを作成できることを検証する。"""
        chunk = DocumentChunk(
            chunk_id="c1",
            text="サンプルテキスト",
            source="test.pdf",
            page=1,
        )
        assert chunk.chunk_id == "c1"
        assert chunk.source == "test.pdf"
        assert chunk.page == 1
        assert chunk.metadata == {}

    def test_default_page_is_none(self) -> None:
        """page のデフォルトが None であることを検証する。"""
        chunk = DocumentChunk(
            chunk_id="c2",
            text="テキスト",
            source="test.pdf",
        )
        assert chunk.page is None


# ---------------------------------------------------------------------------
# SearchResult
# ---------------------------------------------------------------------------


class TestSearchResult:
    """SearchResult のテスト"""

    def test_create_result(self) -> None:
        """検索結果を作成できることを検証する。"""
        chunk = DocumentChunk(
            chunk_id="c1",
            text="テキスト",
            source="test.pdf",
        )
        result = SearchResult(chunk=chunk, score=0.95)
        assert result.score == 0.95
        assert result.chunk.chunk_id == "c1"


# ---------------------------------------------------------------------------
# Subtask / TaskPlanningResult
# ---------------------------------------------------------------------------


class TestTaskPlanningResult:
    """TaskPlanningResult のテスト"""

    def test_create_planning_result(self) -> None:
        """タスク分割結果を作成できることを検証する。"""
        result = TaskPlanningResult(
            subtasks=[
                Subtask(
                    purpose="振動試験の結果を調べる",
                    queries=["振動試験 結果", "振動 試験データ"],
                ),
            ],
        )
        assert len(result.subtasks) == 1
        assert result.subtasks[0].purpose == "振動試験の結果を調べる"
        assert len(result.subtasks[0].queries) == 2


# ---------------------------------------------------------------------------
# JudgeResult — @model_validator テスト
# ---------------------------------------------------------------------------


class TestJudgeResult:
    """JudgeResult の @model_validator テスト"""

    def test_sufficient_true_clears_additional_subtasks(self) -> None:
        """sufficient=True の場合、additional_subtasks が None に
        強制されることを検証する。"""
        result = JudgeResult(
            sufficient=True,
            reason="十分な情報があります",
            additional_subtasks=[
                Subtask(purpose="追加調査", queries=["クエリ"]),
            ],
        )
        assert result.sufficient is True
        assert result.additional_subtasks is None

    def test_sufficient_false_with_no_subtasks_becomes_true(self) -> None:
        """sufficient=False かつ additional_subtasks が None の場合、
        sufficient=True に自動補正されることを検証する。"""
        result = JudgeResult(
            sufficient=False,
            reason="情報が不足しています",
            additional_subtasks=None,
        )
        assert result.sufficient is True
        assert "現状の情報で回答します" in result.reason
        assert result.additional_subtasks is None

    def test_sufficient_false_with_empty_list_becomes_true(self) -> None:
        """sufficient=False かつ additional_subtasks が空リストの場合、
        sufficient=True に自動補正されることを検証する。"""
        result = JudgeResult(
            sufficient=False,
            reason="情報が不足しています",
            additional_subtasks=[],
        )
        assert result.sufficient is True
        assert "現状の情報で回答します" in result.reason

    def test_sufficient_false_with_subtasks_stays_false(self) -> None:
        """sufficient=False かつ additional_subtasks がある場合、
        そのまま維持されることを検証する。"""
        subtasks = [Subtask(purpose="追加調査", queries=["追加クエリ"])]
        result = JudgeResult(
            sufficient=False,
            reason="情報が不足しています",
            additional_subtasks=subtasks,
        )
        assert result.sufficient is False
        assert result.additional_subtasks is not None
        assert len(result.additional_subtasks) == 1

    def test_reason_preserved_on_sufficient_true(self) -> None:
        """sufficient=True の場合、reason が変更されないことを検証する。"""
        result = JudgeResult(
            sufficient=True,
            reason="十分です",
        )
        assert result.reason == "十分です"
