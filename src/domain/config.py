"""ハイパーパラメータの一元管理"""

from pydantic import Field
from pydantic_settings import BaseSettings


class WorkflowConfig(BaseSettings):
    """Agentic RAG ワークフローのハイパーパラメータ"""

    # --- ループ制御 ---
    max_loop_count: int = Field(
        default=2,
        description="judge → doc_search 再調査ループの上限回数",
    )

    # --- LLM 基本パラメータ ---
    llm_model_name: str = Field(
        default="gpt-oss:20b",
        description="Ollama LLM モデル名",
    )
    llm_num_ctx: int = Field(
        default=16384,
        description="コンテキストウィンドウサイズ",
    )
    llm_temperature: float = Field(
        default=0.8,
        description="デフォルト Temperature",
    )
    llm_top_k: int = Field(default=40, description="Top-K サンプリング")
    llm_top_p: float = Field(default=0.9, description="Top-P サンプリング")
    llm_repeat_penalty: float = Field(
        default=1.1,
        description="繰り返しペナルティ",
    )

    # --- ノードごとの推論パラメータ ---
    reasoning_task_planning: str = Field(
        default="low",
        description="task_planning の推論強度",
    )
    reasoning_summarize: str = Field(
        default="low",
        description="summarize の推論強度",
    )
    reasoning_judge: str = Field(
        default="low",
        description="judge の推論強度",
    )
    reasoning_generate_answer: str = Field(
        default="medium",
        description="generate_answer の推論強度",
    )

    # --- 構造化出力制御 ---
    structured_output_timeout: float = Field(
        default=120.0,
        description="構造化出力のタイムアウト（秒）",
    )
    structured_output_num_predict: int = Field(
        default=4096,
        description="構造化出力の最大トークン数",
    )
    summarize_timeout: float = Field(
        default=180.0,
        description="要約のタイムアウト（秒）",
    )
    summarize_num_predict: int = Field(
        default=4096,
        description="要約の最大トークン数",
    )

    # --- 検索パラメータ ---
    retrieval_top_k: int = Field(
        default=20,
        description="ハイブリッド検索の取得件数",
    )
    rerank_top_k: int = Field(
        default=5,
        description="Reranking 後の上位件数",
    )
    bm25_weight: float = Field(
        default=0.3,
        description="RRF ハイブリッド検索における BM25 の重み",
    )
    max_return_chars: int = Field(
        default=8000,
        description="検索結果の最大文字数",
    )

    # --- チャンク分割パラメータ ---
    chunk_size: int = Field(default=500, description="チャンクサイズ（文字数）")
    chunk_overlap: int = Field(
        default=100,
        description="チャンクオーバーラップ（文字数）",
    )
    block_max_bytes: int = Field(
        default=40000,
        description="spaCy 分割前のブロック最大バイト数",
    )

    # --- Embedding / Reranker モデル ---
    embedding_model_name: str = Field(
        default="cl-nagoya/ruri-v3-310m",
        description="Embedding モデル名",
    )
    reranker_model_name: str = Field(
        default="cl-nagoya/ruri-v3-reranker-310m",
        description="Reranker モデル名",
    )

    # --- システムプロンプト ---
    system_prompt_task_planning: str = Field(
        default=(
            "あなたはリサーチプランナーです。\n"
            "ユーザの質問に回答するために、ナレッジベース（技術文書）を"
            "検索するためのサブタスクを作成してください。\n\n"
            "サブタスクは最大3個までとしてください。\n"
            "purpose は判定ステップで「この目的に十分な情報が得られたか」を"
            "評価する基準になります。\n"
            "具体的かつ明確に書いてください。\n"
            "検索クエリは、技術文書から関連情報を検索するための"
            "日本語の具体的なフレーズにしてください。"
        ),
        description="タスク分割ノードのシステムプロンプト",
    )
    system_prompt_summarize: str = Field(
        default=(
            "あなたは検索結果を要約するアシスタントです。\n"
            "以下の検索結果を、ユーザの質問に回答するために必要な情報に絞って"
            "日本語で要約してください。\n\n"
            "要約のルール:\n"
            "- 各【目的】ごとに、得られた主要な情報を箇条書きで整理する。\n"
            "- 数値・固有名詞・技術用語は正確に保持する。\n"
            "- 情報が不足している目的があれば、「情報不足」と明記する。\n"
            "- 要約全体を800文字以内に収める。"
        ),
        description="要約ノードのシステムプロンプト",
    )
    system_prompt_judge: str = Field(
        default=(
            "あなたはリサーチの品質を判定する審査員です。\n"
            "ユーザの質問と、検索結果の要約を見て、回答に十分な情報があるか"
            "判断してください。\n\n"
            "# 重要なルール\n"
            "- reason フィールドは必ず日本語で出力してください。\n"
            "- 英語の検索結果が含まれていても、判定理由は日本語で書いてください。\n\n"
            "sufficient が true なら回答作成に進みます。\n"
            "sufficient が false なら、不足している目的について "
            "additional_subtasks を生成してください。"
        ),
        description="十分性判定ノードのシステムプロンプト",
    )
    system_prompt_generate_answer: str = Field(
        default=(
            "あなたはリサーチ結果をもとに回答するAIアシスタントです。\n"
            "検索結果を参考に、ユーザの質問に日本語で丁寧に回答してください。\n"
            "回答は必ず検索結果に基づいて作成し、検索結果に含まれない情報は"
            "含めないでください。\n"
            "回答の最後に、以下の形式で結論をまとめてください。\n\n"
            "# 結論\n"
            "- ユーザの質問: （質問内容）\n"
            "- 回答: （簡潔な回答）"
        ),
        description="回答生成ノードのシステムプロンプト",
    )
    system_prompt_user_default: str = Field(
        default="日本語で回答してください。",
        description="Gradio UI のデフォルトシステムプロンプト（ユーザーが編集可能）",
    )

    model_config = {"env_prefix": "RAG_"}
