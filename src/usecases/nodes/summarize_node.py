"""検索結果要約ノード"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from domain.config import WorkflowConfig
    from domain.ports.llm_port import LLMPort

logger = logging.getLogger(__name__)

WorkflowState = dict[str, Any]


def create_summarize_node(
    llm: LLMPort,
    config: WorkflowConfig,
) -> Callable[[WorkflowState], Awaitable[dict]]:
    """検索結果要約ノードのファクトリ関数"""

    async def summarize_node(state: WorkflowState) -> dict:
        """検索結果を要約し、judge の入力コンテキストを削減する。"""
        question = state["question"]
        search_results = state.get("search_results", [])

        if not search_results:
            logger.warning("検索結果が空のため、要約をスキップします。")
            return {"summary": "検索結果なし"}

        results_text = "\n\n".join(search_results)

        messages = [
            {"role": "system", "content": config.system_prompt_summarize},
            {
                "role": "user",
                "content": (
                    f"## ユーザの質問\n{question}\n\n## 検索結果\n{results_text}"
                ),
            },
        ]

        try:
            response = await asyncio.wait_for(
                llm.agenerate(
                    messages,
                    num_predict=config.summarize_num_predict,
                    reasoning=config.reasoning_summarize,
                ),
                timeout=config.summarize_timeout,
            )
            summary = response.content
        except asyncio.TimeoutError:
            logger.warning("要約がタイムアウトしました。検索結果をそのまま使用します。")
            summary = results_text
        except Exception:
            logger.warning(
                "要約で例外が発生しました。検索結果をそのまま使用します。",
                exc_info=True,
            )
            summary = results_text

        logger.info("要約完了: %d 文字", len(summary))
        return {"summary": summary}

    return summarize_node
