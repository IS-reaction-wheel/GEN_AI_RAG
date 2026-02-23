"""ドキュメント検索ノード（ハイブリッド検索 + Reranking）"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from domain.config import WorkflowConfig
    from domain.ports.reranker_port import RerankerPort
    from domain.ports.vectorstore_port import VectorStorePort

logger = logging.getLogger(__name__)

WorkflowState = dict[str, Any]


def _hybrid_search_rrf(
    query: str,
    vectorstore: VectorStorePort,
    top_k: int,
    bm25_weight: float,
) -> list:
    """ハイブリッド検索（RRF によるスコア統合）を実行する。"""
    vec_results = vectorstore.similarity_search(query, k=top_k)
    bm25_results = vectorstore.keyword_search(query, k=top_k)

    # RRF スコアの計算
    rrf_scores: dict[str, float] = {}
    chunk_map: dict[str, object] = {}
    k_param = 60  # RRF の定数

    vec_weight = 1.0 - bm25_weight

    for rank, r in enumerate(vec_results):
        cid = r.chunk.chunk_id
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + vec_weight / (k_param + rank + 1)
        chunk_map[cid] = r

    for rank, r in enumerate(bm25_results):
        cid = r.chunk.chunk_id
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + bm25_weight / (k_param + rank + 1)
        if cid not in chunk_map:
            chunk_map[cid] = r

    # スコア順にソート
    sorted_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)
    return [chunk_map[cid] for cid in sorted_ids[:top_k]]


def create_doc_search_node(
    vectorstore: VectorStorePort,
    reranker: RerankerPort,
    config: WorkflowConfig,
) -> Callable[[WorkflowState], dict]:
    """ドキュメント検索ノードのファクトリ関数"""

    def doc_search_node(state: WorkflowState) -> dict:
        """各サブタスクの検索クエリでハイブリッド検索 + Reranking を実行する。"""
        subtasks = state.get("subtasks", [])
        existing_results = state.get("search_results", [])

        all_results: list[str] = list(existing_results)

        for st in subtasks:
            purpose = st.get("purpose", "")
            queries = st.get("queries", [])
            purpose_results: list[str] = []

            for query in queries:
                logger.info("検索実行: query=%s", query)
                hybrid_results = _hybrid_search_rrf(
                    query,
                    vectorstore,
                    top_k=config.retrieval_top_k,
                    bm25_weight=config.bm25_weight,
                )

                reranked = reranker.rerank(
                    query,
                    hybrid_results,
                    top_k=config.rerank_top_k,
                )

                for r in reranked:
                    text = r.chunk.text[: config.max_return_chars]
                    purpose_results.append(text)

            if purpose_results:
                header = f"【目的: {purpose}】\n"
                body = "\n---\n".join(purpose_results)
                all_results.append(header + body)

        logger.info("検索結果ブロック数: %d", len(all_results))
        return {"search_results": all_results, "subtasks": []}

    return doc_search_node
