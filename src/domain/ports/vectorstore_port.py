"""ベクトルストアのインターフェース"""

from typing import Protocol

from domain.models import DocumentChunk, SearchResult


class VectorStorePort(Protocol):
    """ベクトルストアのインターフェース"""

    def add_documents(self, chunks: list[DocumentChunk]) -> None:
        """ドキュメントチャンクをベクトル DB に追加する"""
        ...

    def similarity_search(
        self,
        query: str,
        k: int = 10,
    ) -> list[SearchResult]:
        """ベクトル類似度検索を実行する"""
        ...

    def keyword_search(
        self,
        query: str,
        k: int = 10,
    ) -> list[SearchResult]:
        """キーワード検索（BM25）を実行する"""
        ...
