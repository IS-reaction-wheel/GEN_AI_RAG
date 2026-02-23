"""十分性判定ノード（自己修正判定）"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from domain.models import JudgeResult

if TYPE_CHECKING:
    from domain.config import WorkflowConfig
    from domain.ports.llm_port import LLMPort

logger = logging.getLogger(__name__)

WorkflowState = dict[str, Any]


def create_judge_node(
    llm: LLMPort,
    config: WorkflowConfig,
) -> Callable[[WorkflowState], Awaitable[dict]]:
    """十分性判定ノードのファクトリ関数"""

    async def judge_node(state: WorkflowState) -> dict:
        """検索結果の要約から情報の十分性を判定する。"""
        question = state["question"]
        summary = state.get("summary", "")
        loop_count = state.get("loop_count", 0)

        logger.info("十分性判定を開始 (loop_count=%d)", loop_count)

        messages = [
            {"role": "system", "content": config.system_prompt_judge},
            {
                "role": "user",
                "content": (
                    f"## ユーザの質問\n{question}\n\n## 検索結果の要約\n{summary}"
                ),
            },
        ]

        try:
            result: JudgeResult = await asyncio.wait_for(
                llm.agenerate_structured(
                    messages,
                    JudgeResult,
                    num_predict=config.structured_output_num_predict,
                    reasoning=config.reasoning_judge,
                ),
                timeout=config.structured_output_timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "判定がタイムアウトしました。十分と判定して回答生成に進みます。"
            )
            result = JudgeResult(
                sufficient=True,
                reason="判定がタイムアウトしたため、現状の情報で回答します",
            )
        except Exception:
            logger.warning(
                "判定で例外が発生しました。十分と判定して回答生成に進みます。",
                exc_info=True,
            )
            result = JudgeResult(
                sufficient=True,
                reason="判定で例外が発生したため、現状の情報で回答します",
            )

        logger.info(
            "判定結果: sufficient=%s, reason=%s",
            result.sufficient,
            result.reason,
        )

        new_loop_count = loop_count + 1

        if result.sufficient or new_loop_count >= config.max_loop_count:
            if not result.sufficient:
                logger.info(
                    "ループ上限 (%d) に到達。現状の情報で回答生成に進みます。",
                    config.max_loop_count,
                )
            return {"subtasks": [], "loop_count": new_loop_count}

        # 情報不足: 追加サブタスクを設定
        additional = [st.model_dump() for st in (result.additional_subtasks or [])]
        logger.info("追加サブタスク数: %d", len(additional))
        return {"subtasks": additional, "loop_count": new_loop_count}

    return judge_node
