"""Reranker のインターフェース"""

from typing import Protocol

from domain.models import SearchResult


class RerankerPort(Protocol):
    """検索結果を Reranker モデルで再ランキングするインターフェース"""

    def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int = 5,
    ) -> list[SearchResult]:
        """検索結果を Reranker モデルで再ランキングする"""
        ...
