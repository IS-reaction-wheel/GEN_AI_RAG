"""共通テストフィクスチャ（モック定義）"""

from __future__ import annotations

from typing import AsyncIterator

import pytest

from domain.config import WorkflowConfig
from domain.models import DocumentChunk, SearchResult, Subtask, TaskPlanningResult
from domain.ports.llm_port import ChatResponse


# ---------------------------------------------------------------------------
# テスト用 WorkflowConfig
# ---------------------------------------------------------------------------


@pytest.fixture()
def test_config() -> WorkflowConfig:
    """テスト用のデフォルト WorkflowConfig を返す。"""
    return WorkflowConfig()


# ---------------------------------------------------------------------------
# テスト用ドメインオブジェクト
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_chunk() -> DocumentChunk:
    """テスト用の DocumentChunk を返す。"""
    return DocumentChunk(
        chunk_id="test-chunk-1",
        text="ホイールの振動試験において、共振周波数は 120Hz であった。",
        source="test_report.pdf",
        page=1,
    )


@pytest.fixture()
def sample_search_result(sample_chunk: DocumentChunk) -> SearchResult:
    """テスト用の SearchResult を返す。"""
    return SearchResult(chunk=sample_chunk, score=0.95)


# ---------------------------------------------------------------------------
# MockLLM
# ---------------------------------------------------------------------------


class MockLLM:
    """LLMPort のモック実装"""

    def __init__(
        self,
        *,
        generate_response: str = "モック応答テキスト",
        thinking: str = "",
        structured_response: object | None = None,
        stream_tokens: list[str] | None = None,
    ) -> None:
        self._generate_response = generate_response
        self._thinking = thinking
        self._structured_response = structured_response
        self._stream_tokens = stream_tokens or ["モック", "ストリーミング", "応答"]

    async def agenerate(
        self,
        messages: list[dict],
        *,
        num_predict: int | None = None,
        reasoning: str | None = None,
    ) -> ChatResponse:
        return ChatResponse(
            content=self._generate_response,
            thinking=self._thinking,
        )

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
        # デフォルト: TaskPlanningResult を返す
        return TaskPlanningResult(
            subtasks=[
                Subtask(
                    purpose="基本調査",
                    queries=["テストクエリ"],
                ),
            ],
        )

    async def astream(
        self,
        messages: list[dict],
        *,
        reasoning: str | None = None,
    ) -> AsyncIterator[str]:
        for token in self._stream_tokens:
            yield token


@pytest.fixture()
def mock_llm() -> MockLLM:
    """デフォルトの MockLLM を返す。"""
    return MockLLM()


# ---------------------------------------------------------------------------
# MockVectorStore
# ---------------------------------------------------------------------------


class MockVectorStore:
    """VectorStorePort のモック実装"""

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


@pytest.fixture()
def mock_vectorstore() -> MockVectorStore:
    """デフォルトの MockVectorStore を返す。"""
    return MockVectorStore()


# ---------------------------------------------------------------------------
# MockReranker
# ---------------------------------------------------------------------------


class MockReranker:
    """RerankerPort のモック実装"""

    def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int = 5,
    ) -> list[SearchResult]:
        return results[:top_k]


@pytest.fixture()
def mock_reranker() -> MockReranker:
    """デフォルトの MockReranker を返す。"""
    return MockReranker()


# ---------------------------------------------------------------------------
# MockDataLoader
# ---------------------------------------------------------------------------


class MockDataLoader:
    """DataLoaderPort のモック実装"""

    def __init__(
        self,
        chunks: list[DocumentChunk] | None = None,
    ) -> None:
        self._chunks = chunks or [
            DocumentChunk(
                chunk_id="mock-1",
                text="モックチャンク1",
                source="mock.pdf",
                page=1,
            ),
            DocumentChunk(
                chunk_id="mock-2",
                text="モックチャンク2",
                source="mock.pdf",
                page=2,
            ),
        ]

    def load(self, file_path: str) -> list[DocumentChunk]:
        return self._chunks


@pytest.fixture()
def mock_dataloader() -> MockDataLoader:
    """デフォルトの MockDataLoader を返す。"""
    return MockDataLoader()
