"""LangGraph ワークフローグラフ定義"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from usecases.nodes.doc_search_node import create_doc_search_node
from usecases.nodes.generate_answer_node import create_generate_answer_node
from usecases.nodes.judge_node import create_judge_node
from usecases.nodes.summarize_node import create_summarize_node
from usecases.nodes.task_planning_node import create_task_planning_node

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph

    from domain.config import WorkflowConfig
    from domain.ports.llm_port import LLMPort
    from domain.ports.reranker_port import RerankerPort
    from domain.ports.vectorstore_port import VectorStorePort

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """Agentic RAG ワークフローの状態"""

    question: str
    subtasks: list[dict]
    search_results: list[str]
    summary: str
    answer: str
    loop_count: int
    chat_history: list[dict]


def _should_continue(state: dict[str, Any]) -> str:
    """judge ノードの後の条件分岐"""
    if state.get("subtasks"):
        return "doc_search"
    return "generate_answer"


class AgentWorkflow:
    """Agentic RAG ワークフローの構築・実行"""

    def __init__(
        self,
        llm: LLMPort,
        vectorstore: VectorStorePort,
        reranker: RerankerPort,
        config: WorkflowConfig,
    ) -> None:
        self._llm = llm
        self._vectorstore = vectorstore
        self._reranker = reranker
        self._config = config
        self._checkpointer = MemorySaver()
        self._graph = self._build_graph()

    def _build_graph(self) -> CompiledStateGraph:
        """LangGraph グラフを構築してコンパイルする。"""
        graph = StateGraph(WorkflowState)

        # ノードの登録
        graph.add_node(
            "task_planning",
            create_task_planning_node(self._llm, self._config),
        )
        graph.add_node(
            "doc_search",
            create_doc_search_node(
                self._vectorstore,
                self._reranker,
                self._config,
            ),
        )
        graph.add_node(
            "summarize",
            create_summarize_node(self._llm, self._config),
        )
        graph.add_node(
            "judge",
            create_judge_node(self._llm, self._config),
        )
        graph.add_node(
            "generate_answer",
            create_generate_answer_node(self._llm, self._config),
        )

        # エッジの定義
        graph.add_edge(START, "task_planning")
        graph.add_edge("task_planning", "doc_search")
        graph.add_edge("doc_search", "summarize")
        graph.add_edge("summarize", "judge")
        graph.add_conditional_edges(
            "judge",
            _should_continue,
            {"doc_search": "doc_search", "generate_answer": "generate_answer"},
        )
        graph.add_edge("generate_answer", END)

        return graph.compile(checkpointer=self._checkpointer)

    async def ainvoke(
        self,
        question: str,
        chat_history: list[dict] | None = None,
        thread_id: str = "default",
    ) -> dict[str, Any]:
        """ワークフローを非同期実行する。"""
        initial_state: dict[str, Any] = {
            "question": question,
            "subtasks": [],
            "search_results": [],
            "summary": "",
            "answer": "",
            "loop_count": 0,
            "chat_history": chat_history or [],
        }
        config = {"configurable": {"thread_id": thread_id}}
        result = await self._graph.ainvoke(initial_state, config=config)
        return dict(result)

    @property
    def graph(self) -> CompiledStateGraph:
        """コンパイル済みグラフを返す。"""
        return self._graph
