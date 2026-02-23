"""Sentence Transformers Reranker アダプタ（RerankerPort の実装）"""

from __future__ import annotations

import logging

from sentence_transformers import CrossEncoder

from domain.models import SearchResult

logger = logging.getLogger(__name__)


class RerankerAdapter:
    """CrossEncoder を使用した RerankerPort の具体実装"""

    def __init__(self, model_name: str) -> None:
        self._model = CrossEncoder(model_name)
        logger.info("Reranker モデルをロード: %s", model_name)

    def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int = 5,
    ) -> list[SearchResult]:
        """検索結果を Reranker モデルで再ランキングする"""
        if not results:
            return []

        pairs = [[query, r.chunk.text] for r in results]
        scores = self._model.predict(pairs)

        scored = sorted(
            zip(results, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        return [SearchResult(chunk=r.chunk, score=float(s)) for r, s in scored[:top_k]]
