"""AgentWorkflow 全体フローの統合テスト（モック注入）"""

from typing import AsyncIterator

import pytest

from domain.config import WorkflowConfig
from domain.models import (
    DocumentChunk,
    JudgeResult,
    SearchResult,
    Subtask,
    TaskPlanningResult,
)
from domain.ports.llm_port import ChatResponse
from usecases.agent_workflow import AgentWorkflow


# ---------------------------------------------------------------------------
# モック実装
# ---------------------------------------------------------------------------


class _MockLLM:
    """LLMPort のモック（ワークフロー全体テスト用）"""

    def __init__(self) -> None:
        self._call_count = 0

    async def agenerate(
        self,
        messages: list[dict],
        *,
        num_predict: int | None = None,
        reasoning: str | None = None,
    ) -> ChatResponse:
        return ChatResponse(
            content="要約: テスト結果に基づく要約です。",
            thinking="thinking log",
        )

    async def agenerate_structured(
        self,
        messages: list[dict],
        response_model: type,
        *,
        num_predict: int | None = None,
        reasoning: str | None = None,
    ) -> object:
        self._call_count += 1
        if response_model is TaskPlanningResult:
            return TaskPlanningResult(
                subtasks=[
                    Subtask(purpose="基本調査", queries=["テストクエリ"]),
                ],
            )
        if response_model is JudgeResult:
            return JudgeResult(
                sufficient=True,
                reason="十分な情報があります",
            )
        return None

    async def astream(
        self,
        messages: list[dict],
        *,
        reasoning: str | None = None,
    ) -> AsyncIterator[str]:
        for token in ["テスト", "回答", "です。"]:
            yield token


class _MockVectorStore:
    """VectorStorePort のモック"""

    def __init__(self) -> None:
        self.stored_chunks: list[DocumentChunk] = []

    def add_documents(self, chunks: list[DocumentChunk]) -> None:
        self.stored_chunks.extend(chunks)

    def similarity_search(
        self,
        query: str,
        k: int = 10,
    ) -> list[SearchResult]:
        return [
            SearchResult(
                chunk=DocumentChunk(
                    chunk_id="vec-1",
                    text=f"ベクトル検索結果: {query}",
                    source="test.pdf",
                    page=1,
                ),
                score=0.9,
            ),
        ]

    def keyword_search(
        self,
        query: str,
        k: int = 10,
    ) -> list[SearchResult]:
        return [
            SearchResult(
                chunk=DocumentChunk(
                    chunk_id="bm25-1",
                    text=f"BM25 検索結果: {query}",
                    source="test.pdf",
                    page=2,
                ),
                score=0.8,
            ),
        ]


class _MockReranker:
    """RerankerPort のモック"""

    def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int = 5,
    ) -> list[SearchResult]:
        return results[:top_k]


# ---------------------------------------------------------------------------
# テスト
# ---------------------------------------------------------------------------


class TestAgentWorkflow:
    """AgentWorkflow 全体フローのテスト"""

    @pytest.mark.asyncio()
    async def test_full_workflow_sufficient(self) -> None:
        """情報が十分な場合、1ループで回答が生成されることを検証する。"""
        config = WorkflowConfig()
        workflow = AgentWorkflow(
            llm=_MockLLM(),
            vectorstore=_MockVectorStore(),
            reranker=_MockReranker(),
            config=config,
        )

        result = await workflow.ainvoke(
            question="テスト質問",
            thread_id="test-thread-1",
        )

        assert result["answer"] == "テスト回答です。"
        assert result["question"] == "テスト質問"
        assert result["loop_count"] == 1

    @pytest.mark.asyncio()
    async def test_workflow_with_retry(self) -> None:
        """情報が不十分な場合、再検索ループが実行されることを検証する。"""

        class _RetryLLM(_MockLLM):
            def __init__(self) -> None:
                super().__init__()
                self._judge_call_count = 0

            async def agenerate_structured(
                self,
                messages: list[dict],
                response_model: type,
                *,
                num_predict: int | None = None,
                reasoning: str | None = None,
            ) -> object:
                if response_model is TaskPlanningResult:
                    return TaskPlanningResult(
                        subtasks=[
                            Subtask(purpose="基本調査", queries=["クエリ"]),
                        ],
                    )
                if response_model is JudgeResult:
                    self._judge_call_count += 1
                    if self._judge_call_count == 1:
                        # 1回目: 情報不足
                        return JudgeResult(
                            sufficient=False,
                            reason="情報が不足しています",
                            additional_subtasks=[
                                Subtask(purpose="追加調査", queries=["追加クエリ"]),
                            ],
                        )
                    # 2回目: 十分
                    return JudgeResult(
                        sufficient=True,
                        reason="十分になりました",
                    )
                return None

        config = WorkflowConfig(max_loop_count=3)
        workflow = AgentWorkflow(
            llm=_RetryLLM(),
            vectorstore=_MockVectorStore(),
            reranker=_MockReranker(),
            config=config,
        )

        result = await workflow.ainvoke(
            question="テスト質問",
            thread_id="test-thread-2",
        )

        assert result["answer"] == "テスト回答です。"
        assert result["loop_count"] == 2  # 2回ループした
