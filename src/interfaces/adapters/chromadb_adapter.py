"""Chroma DB アダプタ（VectorStorePort の実装）"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import chromadb

from domain.models import DocumentChunk, SearchResult

logger = logging.getLogger(__name__)


class ChromaDBAdapter:
    """Chroma DB + BM25 による VectorStorePort の具体実装"""

    def __init__(
        self,
        embedding_fn: Callable[[list[str]], list[list[float]]],
        collection_name: str = "rag_collection",
        tokenize_fn: Callable[[str], list[str]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn
        self._tokenize_fn = tokenize_fn
        self._client = chromadb.Client()
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        # BM25 用のドキュメントキャッシュ
        self._chunks_cache: list[DocumentChunk] = []
        self._bm25_index: Any | None = None

    def add_documents(self, chunks: list[DocumentChunk]) -> None:
        """ドキュメントチャンクをベクトル DB に追加する"""
        if not chunks:
            return

        texts = [c.text for c in chunks]
        ids = [c.chunk_id for c in chunks]
        metadatas = [
            {"source": c.source, "page": c.page or 0, **c.metadata} for c in chunks
        ]

        embeddings = self._embedding_fn(texts)

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        self._chunks_cache.extend(chunks)
        self._rebuild_bm25_index()

        logger.info("Chroma DB に %d チャンクを追加しました", len(chunks))

    def _rebuild_bm25_index(self) -> None:
        """BM25 インデックスを再構築する。"""
        if not self._chunks_cache or self._tokenize_fn is None:
            self._bm25_index = None
            return

        try:
            from rank_bm25 import BM25Okapi

            tokenized = [self._tokenize_fn(c.text) for c in self._chunks_cache]
            self._bm25_index = BM25Okapi(tokenized)
        except ImportError:
            logger.warning(
                "rank_bm25 が利用できないため、BM25 インデックスを構築できません"
            )
            self._bm25_index = None

    def similarity_search(
        self,
        query: str,
        k: int = 10,
    ) -> list[SearchResult]:
        """ベクトル類似度検索を実行する"""
        if self._collection.count() == 0:
            return []

        query_embedding = self._embedding_fn([query])[0]

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, self._collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        search_results: list[SearchResult] = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                text = results["documents"][0][i] if results["documents"] else ""
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 1.0
                score = 1.0 - distance  # cosine distance → similarity

                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    text=text,
                    source=metadata.get("source", ""),
                    page=metadata.get("page"),
                    metadata={
                        k: v for k, v in metadata.items() if k not in ("source", "page")
                    },
                )
                search_results.append(SearchResult(chunk=chunk, score=score))

        return search_results

    def keyword_search(
        self,
        query: str,
        k: int = 10,
    ) -> list[SearchResult]:
        """キーワード検索（BM25）を実行する"""
        if (
            self._bm25_index is None
            or self._tokenize_fn is None
            or not self._chunks_cache
        ):
            return []

        query_tokens = self._tokenize_fn(query)
        if not query_tokens:
            return []

        scores = self._bm25_index.get_scores(query_tokens)

        scored_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )[:k]

        search_results: list[SearchResult] = []
        for idx in scored_indices:
            if scores[idx] > 0:
                chunk = self._chunks_cache[idx]
                search_results.append(
                    SearchResult(chunk=chunk, score=float(scores[idx])),
                )

        return search_results
