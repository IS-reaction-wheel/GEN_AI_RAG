"""Gradio UI ハンドラ（チャット・ファイルアップロード・思考過程表示）"""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

import gradio as gr

if TYPE_CHECKING:
    from domain.config import WorkflowConfig
    from domain.ports.llm_port import LLMPort
    from domain.ports.reranker_port import RerankerPort
    from domain.ports.vectorstore_port import VectorStorePort
    from usecases.data_ingestion import DataIngestion

logger = logging.getLogger(__name__)


class GradioHandler:
    """Gradio UI のイベントハンドリング

    notebook 07 と同様に、各ノードを個別に呼び出して
    思考過程のリアルタイム表示とストリーミング回答を実現する。
    """

    def __init__(
        self,
        ingestion: DataIngestion,
        config: WorkflowConfig,
        llm: LLMPort,
        vectorstore: VectorStorePort,
        reranker: RerankerPort,
    ) -> None:
        self._ingestion = ingestion
        self._config = config
        self._llm = llm

        # ノードファクトリからノード関数を生成
        from usecases.nodes.doc_search_node import create_doc_search_node
        from usecases.nodes.judge_node import create_judge_node
        from usecases.nodes.summarize_node import create_summarize_node
        from usecases.nodes.task_planning_node import create_task_planning_node

        self._task_planning = create_task_planning_node(llm, config)
        self._doc_search = create_doc_search_node(vectorstore, reranker, config)
        self._summarize = create_summarize_node(llm, config)
        self._judge = create_judge_node(llm, config)

    async def respond(
        self,
        message: str,
        history: list[dict],
        system_prompt: str,
        temperature: float,
        thinking_log: str,
        session_state: dict,
    ) -> AsyncIterator[tuple[list[dict], str, dict]]:
        """チャット応答を段階的にストリーミング生成する。

        notebook 07 と同様に各ノードを個別に呼び出し、
        各ステップで yield して思考過程をリアルタイム表示する。
        最終回答はトークン単位でストリーミングする。
        """
        thread_id = session_state.get("thread_id", str(uuid.uuid4()))
        session_state["thread_id"] = thread_id

        # ユーザーメッセージを履歴に追加
        history = list(history) + [{"role": "user", "content": message}]

        # 前回の思考過程に区切り線を追加
        if thinking_log.strip():
            thinking_log = thinking_log.rstrip("\n") + "\n\n" + "─" * 40 + "\n"

        # ワークフロー状態の初期化
        state: dict[str, Any] = {
            "question": message,
            "subtasks": [],
            "search_results": [],
            "summary": "",
            "answer": "",
            "loop_count": 0,
        }

        # --- Phase 1: タスク分割 ---
        thinking_log += "📋 タスク分割中...\n"
        yield history, thinking_log, session_state

        try:
            result = await self._task_planning(state)
            state.update(result)
        except Exception:
            logger.exception("タスク分割でエラーが発生しました")
            state["subtasks"] = [{"purpose": "基本調査", "queries": [message]}]

        # サブタスク情報をログに追記
        thinking_log += f"サブタスク数: {len(state['subtasks'])}\n"
        for i, st in enumerate(state["subtasks"]):
            thinking_log += f"  {i + 1}. 目的: {st.get('purpose', '')}\n"
            thinking_log += f"     クエリ: {st.get('queries', [])}\n"
        thinking_log += "\n"
        yield history, thinking_log, session_state

        # --- Phase 2: 検索 + 要約 + 判定ループ ---
        while state["subtasks"]:
            # 検索
            thinking_log += "🔍 ドキュメント検索中...\n"
            yield history, thinking_log, session_state

            try:
                result = self._doc_search(state)
                state.update(result)
            except Exception:
                logger.exception("検索でエラーが発生しました")
                state["subtasks"] = []

            thinking_log += f"  検索結果ブロック数: {len(state['search_results'])}\n\n"
            yield history, thinking_log, session_state

            # ループ上限チェック
            if state["loop_count"] >= self._config.max_loop_count:
                thinking_log += "⚠️ ループ上限に到達 → 回答作成へ\n\n"
                yield history, thinking_log, session_state
                break

            # 要約
            thinking_log += "📝 検索結果を要約中...\n"
            yield history, thinking_log, session_state

            try:
                result = await self._summarize(state)
                state.update(result)
            except Exception:
                logger.exception("要約でエラーが発生しました")
                state["summary"] = "\n\n".join(state["search_results"])

            thinking_log += f"  要約文字数: {len(state['summary'])}\n\n"
            yield history, thinking_log, session_state

            # 判定
            thinking_log += "⚖️ 情報の十分性を判定中...\n"
            yield history, thinking_log, session_state

            try:
                result = await self._judge(state)
                state.update(result)
            except Exception:
                logger.exception("判定でエラーが発生しました")
                state["subtasks"] = []

            if state["subtasks"]:
                thinking_log += "🔄 情報不足 → 再検索\n"
                for i, st in enumerate(state["subtasks"]):
                    thinking_log += (
                        f"  追加 {i + 1}. {st.get('purpose', '')}: "
                        f"{st.get('queries', [])}\n"
                    )
            else:
                thinking_log += "✅ 情報十分 → 回答作成へ\n"
            thinking_log += "\n"
            yield history, thinking_log, session_state

        # --- Phase 3: 回答生成（ストリーミング） ---
        thinking_log += "✏️ 回答を生成中...\n"
        yield history, thinking_log, session_state

        # システムプロンプト構築
        sys_content = (
            system_prompt + "\n\n" + self._config.system_prompt_generate_answer
        )

        # 回答生成には生の検索結果を使用（情報の正確性を保持）
        results_text = "\n\n".join(state["search_results"])

        # マルチターン対応: 直近の会話履歴をコンテキストに含める
        # 現在の質問（末尾1件）は除外し、直近4メッセージ（2往復）まで含める
        recent_history = history[:-1][-4:]
        history_lines: list[str] = []
        for msg in recent_history:
            role = "ユーザ" if msg.get("role") == "user" else "AI"
            content = msg.get("content", "")[:500]
            history_lines.append(f"{role}: {content}")

        user_content = ""
        if history_lines:
            user_content += "会話履歴:\n" + "\n".join(history_lines) + "\n\n"
        user_content += f"質問: {message}\n\n検索結果:\n{results_text}"

        messages = [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": user_content},
        ]

        # ストリーミング回答生成
        history = list(history) + [{"role": "assistant", "content": ""}]
        bot_reply = ""

        try:
            async for token in self._llm.astream(
                messages,
                reasoning=self._config.reasoning_generate_answer,
            ):
                bot_reply += token
                history[-1] = {"role": "assistant", "content": bot_reply}
                yield history, thinking_log, session_state
        except Exception:
            logger.exception("回答生成中にエラーが発生しました")
            if not bot_reply:
                bot_reply = "エラーが発生しました。もう一度お試しください。"
                history[-1] = {"role": "assistant", "content": bot_reply}

        thinking_log += "✅ 回答生成完了\n"
        yield history, thinking_log, session_state

    def upload_file(
        self,
        file: Any,
        session_state: dict,
    ) -> tuple[str, dict]:
        """PDF ファイルをアップロードしてベクトル DB に登録する。"""
        if file is None:
            return "ファイルが選択されていません。", session_state

        try:
            file_path = file.name if hasattr(file, "name") else str(file)
            count = self._ingestion.ingest(file_path)
            status = f"PDF 読み込み完了: {count} チャンク"
            logger.info(status)
            return status, session_state
        except Exception:
            logger.exception("PDF アップロード中にエラーが発生しました")
            return "PDF の読み込みに失敗しました。", session_state

    def clear_chat(
        self,
        session_state: dict,
    ) -> tuple[list, str, dict]:
        """会話履歴をクリアする。"""
        session_state["thread_id"] = str(uuid.uuid4())
        return [], "", session_state

    def launch(self) -> gr.Blocks:
        """Gradio UI を構築して返す。"""
        with gr.Blocks(
            title="RAG チャットアシスタント（AI Agent Workflow + RAG）",
        ) as demo:
            gr.Markdown("### RAG チャットアシスタント（AI Agent Workflow + RAG）")

            session_state = gr.State(value={"thread_id": str(uuid.uuid4())})

            with gr.Row():
                # 左カラム
                with gr.Column(scale=1):
                    file_input = gr.File(
                        label="PDF ファイルをドラッグ＆ドロップ",
                        file_types=[".pdf"],
                    )
                    pdf_status = gr.Textbox(
                        label="PDF ステータス",
                        interactive=False,
                    )
                    thinking_log = gr.Textbox(
                        label="AI の思考過程",
                        interactive=False,
                        lines=25,
                        max_lines=25,
                    )

                # 右カラム
                with gr.Column(scale=1):
                    chatbot = gr.Chatbot(
                        label="AI チャット",
                        height=450,
                    )

                    with gr.Accordion("システムプロンプト設定 (任意)", open=False):
                        system_prompt = gr.Textbox(
                            value=self._config.system_prompt_user_default,
                            label="システムプロンプト",
                            lines=2,
                        )

                    temperature = gr.Slider(
                        minimum=0.0,
                        maximum=1.0,
                        value=self._config.llm_temperature,
                        step=0.1,
                        label="Temperature (低いほど正確、高いほど創造的)",
                    )

                    msg_input = gr.Textbox(
                        label="メッセージを入力",
                        placeholder="質問を入力してください...",
                        lines=2,
                    )

                    with gr.Row():
                        submit_btn = gr.Button("送信", variant="primary")
                        stop_btn = gr.Button("生成を停止", variant="stop")
                        clear_btn = gr.Button("会話をクリア", variant="secondary")

            # イベントハンドラ
            submit_args = {
                "fn": self.respond,
                "inputs": [
                    msg_input,
                    chatbot,
                    system_prompt,
                    temperature,
                    thinking_log,
                    session_state,
                ],
                "outputs": [chatbot, thinking_log, session_state],
            }
            submit_event_click = submit_btn.click(**submit_args)
            submit_event_enter = msg_input.submit(**submit_args)

            # 送信後に入力欄をクリア
            submit_btn.click(fn=lambda: "", outputs=msg_input)
            msg_input.submit(fn=lambda: "", outputs=msg_input)

            # 生成停止ボタン
            stop_btn.click(
                fn=None,
                inputs=None,
                outputs=None,
                cancels=[submit_event_click, submit_event_enter],
            )

            file_input.change(
                fn=self.upload_file,
                inputs=[file_input, session_state],
                outputs=[pdf_status, session_state],
            )

            clear_btn.click(
                fn=self.clear_chat,
                inputs=[session_state],
                outputs=[chatbot, thinking_log, session_state],
            )

        return demo
