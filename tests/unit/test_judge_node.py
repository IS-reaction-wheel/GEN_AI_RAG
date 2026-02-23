"""十分性判定ノードのユニットテスト"""

from typing import AsyncIterator

import pytest

from domain.config import WorkflowConfig
from domain.models import JudgeResult, Subtask
from domain.ports.llm_port import ChatResponse
from usecases.nodes.judge_node import create_judge_node


class _MockLLM:
    """テスト用 LLM モック"""

    def __init__(self, structured_response: object | None = None) -> None:
        self._structured_response = structured_response

    async def agenerate(
        self,
        messages: list[dict],
        *,
        num_predict: int | None = None,
        reasoning: str | None = None,
    ) -> ChatResponse:
        return ChatResponse(content="mock", thinking="")

    async def agenerate_structured(
        self,
        messages: list[dict],
        response_model: type,
        *,
        num_predict: int | None = None,
        reasoning: str | None = None,
    ) -> object:
        if self._structured_response is not None:
            return self._structured_response
        return JudgeResult(sufficient=True, reason="十分な情報があります")

    async def astream(
        self,
        messages: list[dict],
        *,
        reasoning: str | None = None,
    ) -> AsyncIterator[str]:
        yield "mock"


class TestJudgeNode:
    """judge ノードのテスト"""

    @pytest.mark.asyncio()
    async def test_sufficient_true(self, test_config: WorkflowConfig) -> None:
        """情報が十分と判定された場合、subtasks が空になることを検証する。"""
        judge_result = JudgeResult(
            sufficient=True,
            reason="十分な情報があります",
        )
        node = create_judge_node(
            _MockLLM(structured_response=judge_result),
            test_config,
        )

        state = {
            "question": "テスト質問",
            "summary": "要約テキスト",
            "loop_count": 0,
        }
        result = await node(state)

        assert result["subtasks"] == []
        assert result["loop_count"] == 1

    @pytest.mark.asyncio()
    async def test_sufficient_false_with_additional_subtasks(
        self,
        test_config: WorkflowConfig,
    ) -> None:
        """情報が不十分な場合、追加サブタスクが返されることを検証する。"""
        judge_result = JudgeResult(
            sufficient=False,
            reason="情報が不足しています",
            additional_subtasks=[
                Subtask(purpose="追加調査", queries=["追加クエリ"]),
            ],
        )
        node = create_judge_node(
            _MockLLM(structured_response=judge_result),
            test_config,
        )

        state = {
            "question": "テスト質問",
            "summary": "要約テキスト",
            "loop_count": 0,
        }
        result = await node(state)

        assert len(result["subtasks"]) == 1
        assert result["subtasks"][0]["purpose"] == "追加調査"
        assert result["loop_count"] == 1

    @pytest.mark.asyncio()
    async def test_loop_limit_forces_answer(
        self,
        test_config: WorkflowConfig,
    ) -> None:
        """ループ上限到達時に回答生成に進むことを検証する。"""
        judge_result = JudgeResult(
            sufficient=False,
            reason="情報が不足しています",
            additional_subtasks=[
                Subtask(purpose="追加調査", queries=["追加クエリ"]),
            ],
        )
        test_config.max_loop_count = 2
        node = create_judge_node(
            _MockLLM(structured_response=judge_result),
            test_config,
        )

        state = {
            "question": "テスト質問",
            "summary": "要約テキスト",
            "loop_count": 1,  # 次で loop_count=2 → 上限到達
        }
        result = await node(state)

        assert result["subtasks"] == []
        assert result["loop_count"] == 2

    @pytest.mark.asyncio()
    async def test_exception_forces_sufficient(
        self,
        test_config: WorkflowConfig,
    ) -> None:
        """例外発生時に十分と判定されることを検証する。"""

        class _ErrorLLM(_MockLLM):
            async def agenerate_structured(
                self,
                messages: list[dict],
                response_model: type,
                *,
                num_predict: int | None = None,
                reasoning: str | None = None,
            ) -> object:
                raise RuntimeError("LLM error")

        node = create_judge_node(_ErrorLLM(), test_config)

        state = {
            "question": "テスト質問",
            "summary": "要約テキスト",
            "loop_count": 0,
        }
        result = await node(state)

        assert result["subtasks"] == []
