"""ドキュメント検索ノードのユニットテスト"""

from domain.config import WorkflowConfig
from domain.models import DocumentChunk, SearchResult
from usecases.nodes.doc_search_node import create_doc_search_node


class _MockVectorStore:
    """VectorStorePort のモック"""

    def add_documents(self, chunks: list[DocumentChunk]) -> None:
        pass

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


class TestDocSearchNode:
    """doc_search ノードのテスト"""

    def test_normal_search(self, test_config: WorkflowConfig) -> None:
        """サブタスクに基づいて検索結果が返されることを検証する。"""
        node = create_doc_search_node(
            _MockVectorStore(),
            _MockReranker(),
            test_config,
        )
        state = {
            "question": "テスト質問",
            "subtasks": [
                {"purpose": "基本調査", "queries": ["テストクエリ"]},
            ],
            "search_results": [],
        }
        result = node(state)

        assert len(result["search_results"]) > 0
        assert "【目的: 基本調査】" in result["search_results"][0]
        assert result["subtasks"] == []

    def test_multiple_subtasks(self, test_config: WorkflowConfig) -> None:
        """複数サブタスクの検索結果が蓄積されることを検証する。"""
        node = create_doc_search_node(
            _MockVectorStore(),
            _MockReranker(),
            test_config,
        )
        state = {
            "question": "テスト質問",
            "subtasks": [
                {"purpose": "調査1", "queries": ["クエリA"]},
                {"purpose": "調査2", "queries": ["クエリB"]},
            ],
            "search_results": [],
        }
        result = node(state)

        assert len(result["search_results"]) == 2

    def test_existing_results_preserved(self, test_config: WorkflowConfig) -> None:
        """既存の検索結果が保持されることを検証する。"""
        node = create_doc_search_node(
            _MockVectorStore(),
            _MockReranker(),
            test_config,
        )
        state = {
            "question": "テスト質問",
            "subtasks": [
                {"purpose": "追加調査", "queries": ["クエリ"]},
            ],
            "search_results": ["既存の結果"],
        }
        result = node(state)

        assert result["search_results"][0] == "既存の結果"
        assert len(result["search_results"]) == 2

    def test_empty_subtasks(self, test_config: WorkflowConfig) -> None:
        """サブタスクが空の場合、既存結果のみが返されることを検証する。"""
        node = create_doc_search_node(
            _MockVectorStore(),
            _MockReranker(),
            test_config,
        )
        state = {
            "question": "テスト質問",
            "subtasks": [],
            "search_results": ["既存の結果"],
        }
        result = node(state)

        assert result["search_results"] == ["既存の結果"]
