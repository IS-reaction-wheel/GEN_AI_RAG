"""Gradio UI ハンドラ（チャット・ファイルアップロード・思考過程表示）"""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

import gradio as gr

if TYPE_CHECKING:
    from domain.config import WorkflowConfig
    from usecases.agent_workflow import AgentWorkflow
    from usecases.data_ingestion import DataIngestion

logger = logging.getLogger(__name__)


class GradioHandler:
    """Gradio UI のイベントハンドリング"""

    def __init__(
        self,
        workflow: AgentWorkflow,
        ingestion: DataIngestion,
        config: WorkflowConfig,
    ) -> None:
        self._workflow = workflow
        self._ingestion = ingestion
        self._config = config

    async def respond(
        self,
        message: str,
        history: list[dict],
        system_prompt: str,
        temperature: float,
        thinking_log: str,
        session_state: dict,
    ) -> AsyncIterator[tuple[list[dict], str, dict]]:
        """チャット応答をストリーミング生成する。"""
        thread_id = session_state.get("thread_id", str(uuid.uuid4()))
        session_state["thread_id"] = thread_id

        # チャット履歴を構築
        chat_history = [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in history
        ]

        thinking_log += "\n📋 タスク分割中...\n"
        history.append({"role": "user", "content": message})
        yield history, thinking_log, session_state

        try:
            # ワークフロー実行
            thinking_log += "🔍 ドキュメント検索中...\n"
            yield history, thinking_log, session_state

            result = await self._workflow.ainvoke(
                question=message,
                chat_history=chat_history,
                thread_id=thread_id,
            )

            thinking_log += "📝 検索結果を要約中...\n"
            thinking_log += "⚖️ 情報の十分性を判定中...\n"
            thinking_log += "✏️ 回答を生成中...\n"
            yield history, thinking_log, session_state

            answer = result.get("answer", "回答を生成できませんでした。")
            history.append({"role": "assistant", "content": answer})

            thinking_log += "✅ 回答生成完了\n"
            yield history, thinking_log, session_state

        except Exception:
            logger.exception("ワークフロー実行中にエラーが発生しました")
            error_msg = "エラーが発生しました。もう一度お試しください。"
            history.append({"role": "assistant", "content": error_msg})
            thinking_log += "❌ エラーが発生しました\n"
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
            gr.Markdown("# RAG チャットアシスタント（AI Agent Workflow + RAG）")

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
                        lines=15,
                    )

                # 右カラム
                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(
                        label="チャット",
                        type="messages",
                        height=500,
                    )

                    with gr.Accordion("システムプロンプト設定 (任意)", open=False):
                        system_prompt = gr.Textbox(
                            value=self._config.system_prompt_user_default,
                            label="システムプロンプト",
                            lines=3,
                        )

                    temperature = gr.Slider(
                        minimum=0.0,
                        maximum=1.0,
                        value=self._config.llm_temperature,
                        step=0.1,
                        label="Temperature",
                    )

                    msg_input = gr.Textbox(
                        label="ここに質問を入力...",
                        lines=2,
                    )

                    with gr.Row():
                        submit_btn = gr.Button("送信", variant="primary")
                        clear_btn = gr.Button("会話をクリア")

            # イベントハンドラ
            submit_btn.click(
                fn=self.respond,
                inputs=[
                    msg_input,
                    chatbot,
                    system_prompt,
                    temperature,
                    thinking_log,
                    session_state,
                ],
                outputs=[chatbot, thinking_log, session_state],
            ).then(fn=lambda: "", outputs=msg_input)

            msg_input.submit(
                fn=self.respond,
                inputs=[
                    msg_input,
                    chatbot,
                    system_prompt,
                    temperature,
                    thinking_log,
                    session_state,
                ],
                outputs=[chatbot, thinking_log, session_state],
            ).then(fn=lambda: "", outputs=msg_input)

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
