"""タスク分割ノード（サブタスク・検索クエリ生成）"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from domain.models import TaskPlanningResult

if TYPE_CHECKING:
    from domain.config import WorkflowConfig
    from domain.ports.llm_port import LLMPort

logger = logging.getLogger(__name__)

# LangGraph State の型エイリアス
WorkflowState = dict[str, Any]


def create_task_planning_node(
    llm: LLMPort,
    config: WorkflowConfig,
) -> Callable[[WorkflowState], Awaitable[dict]]:
    """タスク分割ノードのファクトリ関数"""

    async def task_planning_node(state: WorkflowState) -> dict:
        """ユーザーの質問を分析し、サブタスク（目的 + 検索クエリ）を生成する。"""
        question = state["question"]
        logger.info("タスク分割を開始: %s", question)

        messages = [
            {"role": "system", "content": config.system_prompt_task_planning},
            {"role": "user", "content": question},
        ]

        fallback_subtasks = [{"purpose": "基本調査", "queries": [question]}]

        try:
            result: TaskPlanningResult = await asyncio.wait_for(
                llm.agenerate_structured(
                    messages,
                    TaskPlanningResult,
                    num_predict=config.structured_output_num_predict,
                    reasoning=config.reasoning_task_planning,
                ),
                timeout=config.structured_output_timeout,
            )
            subtasks = [st.model_dump() for st in result.subtasks]
            if not subtasks:
                subtasks = fallback_subtasks
        except asyncio.TimeoutError:
            logger.warning(
                "タスク分割がタイムアウトしました。フォールバックを使用します。"
            )
            subtasks = fallback_subtasks
        except Exception:
            logger.warning(
                "タスク分割で例外が発生しました。フォールバックを使用します。",
                exc_info=True,
            )
            subtasks = fallback_subtasks

        logger.info("生成されたサブタスク数: %d", len(subtasks))
        return {"subtasks": subtasks, "loop_count": 0}

    return task_planning_node
