"""最終回答生成ノード（ストリーミング）"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from domain.config import WorkflowConfig
    from domain.ports.llm_port import LLMPort

logger = logging.getLogger(__name__)

WorkflowState = dict[str, Any]


def create_generate_answer_node(
    llm: LLMPort,
    config: WorkflowConfig,
) -> Callable[[WorkflowState], Awaitable[dict]]:
    """最終回答生成ノードのファクトリ関数"""

    async def generate_answer_node(state: WorkflowState) -> dict:
        """検索結果をコンテキストとしてストリーミング回答を生成する。"""
        question = state["question"]
        search_results = state.get("search_results", [])
        chat_history = state.get("chat_history", [])

        context = "\n\n".join(search_results) if search_results else "検索結果なし"

        sys_content = (
            config.system_prompt_user_default
            + "\n\n"
            + config.system_prompt_generate_answer
        )

        messages: list[dict] = [{"role": "system", "content": sys_content}]

        # チャット履歴を追加
        for msg in chat_history:
            messages.append(
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            )

        messages.append(
            {
                "role": "user",
                "content": (f"## 検索結果\n{context}\n\n## ユーザの質問\n{question}"),
            },
        )

        logger.info("回答生成を開始")

        answer_parts: list[str] = []
        try:
            stream = llm.astream(
                messages,
                reasoning=config.reasoning_generate_answer,
            )
            async for token in stream:
                answer_parts.append(token)
        except Exception:
            logger.warning("ストリーミング中に例外が発生しました。", exc_info=True)

        answer = "".join(answer_parts)
        if not answer:
            answer = "回答を生成できませんでした。"

        logger.info("回答生成完了: %d 文字", len(answer))
        return {"answer": answer}

    return generate_answer_node
