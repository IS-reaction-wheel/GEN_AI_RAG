"""検索結果要約ノードのユニットテスト"""

import asyncio
from typing import AsyncIterator

import pytest

from domain.config import WorkflowConfig
from domain.ports.llm_port import ChatResponse
from usecases.nodes.summarize_node import create_summarize_node


class _MockLLM:
    """テスト用 LLM モック"""

    def __init__(self, response: str = "要約されたテキスト") -> None:
        self._response = response

    async def agenerate(
        self,
        messages: list[dict],
        *,
        num_predict: int | None = None,
        reasoning: str | None = None,
    ) -> ChatResponse:
        return ChatResponse(content=self._response, thinking="")

    async def agenerate_structured(
        self,
        messages: list[dict],
        response_model: type,
        *,
        num_predict: int | None = None,
        reasoning: str | None = None,
    ) -> object:
        return None

    async def astream(
        self,
        messages: list[dict],
        *,
        reasoning: str | None = None,
    ) -> AsyncIterator[str]:
        yield "mock"


class TestSummarizeNode:
    """summarize ノードのテスト"""

    @pytest.mark.asyncio()
    async def test_normal_summarize(self, test_config: WorkflowConfig) -> None:
        """正常に要約が生成されることを検証する。"""
        mock_llm = _MockLLM(response="要約結果テキスト")
        node = create_summarize_node(mock_llm, test_config)

        state = {
            "question": "テスト質問",
            "search_results": ["検索結果1", "検索結果2"],
        }
        result = await node(state)

        assert result["summary"] == "要約結果テキスト"

    @pytest.mark.asyncio()
    async def test_empty_search_results(self, test_config: WorkflowConfig) -> None:
        """検索結果が空の場合、要約がスキップされることを検証する。"""
        node = create_summarize_node(_MockLLM(), test_config)

        state = {"question": "テスト質問", "search_results": []}
        result = await node(state)

        assert result["summary"] == "検索結果なし"

    @pytest.mark.asyncio()
    async def test_timeout_uses_raw_results(
        self,
        test_config: WorkflowConfig,
    ) -> None:
        """タイムアウト時に検索結果がそのまま使用されることを検証する。"""

        class _SlowLLM(_MockLLM):
            async def agenerate(
                self,
                messages: list[dict],
                *,
                num_predict: int | None = None,
                reasoning: str | None = None,
            ) -> ChatResponse:
                await asyncio.sleep(999)
                return ChatResponse(content="", thinking="")

        test_config.summarize_timeout = 0.01
        node = create_summarize_node(_SlowLLM(), test_config)

        state = {
            "question": "テスト質問",
            "search_results": ["結果A", "結果B"],
        }
        result = await node(state)

        assert "結果A" in result["summary"]
        assert "結果B" in result["summary"]
