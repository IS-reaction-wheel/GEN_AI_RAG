"""タスク分割ノードのユニットテスト"""

import asyncio
from typing import AsyncIterator

import pytest

from domain.config import WorkflowConfig
from domain.models import Subtask, TaskPlanningResult
from domain.ports.llm_port import ChatResponse
from usecases.nodes.task_planning_node import create_task_planning_node


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
        return TaskPlanningResult(
            subtasks=[Subtask(purpose="基本調査", queries=["テストクエリ"])],
        )

    async def astream(
        self,
        messages: list[dict],
        *,
        reasoning: str | None = None,
    ) -> AsyncIterator[str]:
        yield "mock"


class TestTaskPlanningNode:
    """task_planning ノードのテスト"""

    @pytest.mark.asyncio()
    async def test_normal_execution(self, test_config: WorkflowConfig) -> None:
        """正常にサブタスクが生成されることを検証する。"""
        expected = TaskPlanningResult(
            subtasks=[
                Subtask(purpose="振動試験結果の調査", queries=["振動試験 結果"]),
                Subtask(purpose="共振周波数の確認", queries=["共振周波数"]),
            ],
        )
        mock_llm = _MockLLM(structured_response=expected)
        node = create_task_planning_node(mock_llm, test_config)

        state = {"question": "ホイールの振動試験の結果を教えて"}
        result = await node(state)

        assert len(result["subtasks"]) == 2
        assert result["subtasks"][0]["purpose"] == "振動試験結果の調査"
        assert result["loop_count"] == 0

    @pytest.mark.asyncio()
    async def test_timeout_uses_fallback(
        self,
        test_config: WorkflowConfig,
    ) -> None:
        """タイムアウト時にフォールバックが使用されることを検証する。"""

        class _SlowLLM(_MockLLM):
            async def agenerate_structured(
                self,
                messages: list[dict],
                response_model: type,
                *,
                num_predict: int | None = None,
                reasoning: str | None = None,
            ) -> object:
                await asyncio.sleep(999)
                return TaskPlanningResult(subtasks=[])

        test_config.structured_output_timeout = 0.01
        node = create_task_planning_node(_SlowLLM(), test_config)

        state = {"question": "テスト質問"}
        result = await node(state)

        assert len(result["subtasks"]) == 1
        assert result["subtasks"][0]["purpose"] == "基本調査"
        assert result["subtasks"][0]["queries"] == ["テスト質問"]

    @pytest.mark.asyncio()
    async def test_exception_uses_fallback(
        self,
        test_config: WorkflowConfig,
    ) -> None:
        """例外発生時にフォールバックが使用されることを検証する。"""

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

        node = create_task_planning_node(_ErrorLLM(), test_config)

        state = {"question": "テスト質問"}
        result = await node(state)

        assert len(result["subtasks"]) == 1
        assert result["subtasks"][0]["purpose"] == "基本調査"

    @pytest.mark.asyncio()
    async def test_empty_subtasks_uses_fallback(
        self,
        test_config: WorkflowConfig,
    ) -> None:
        """空のサブタスクリストが返された場合にフォールバックが使用されることを検証する。"""
        empty_result = TaskPlanningResult(subtasks=[])
        mock_llm = _MockLLM(structured_response=empty_result)
        node = create_task_planning_node(mock_llm, test_config)

        state = {"question": "テスト質問"}
        result = await node(state)

        assert len(result["subtasks"]) == 1
        assert result["subtasks"][0]["purpose"] == "基本調査"
