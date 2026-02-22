# ユビキタス言語定義（Glossary）

本ドキュメントは、開発者（AI アシスタント含む）とユーザー（製造業の現場エンジニア）の間で認識のズレを防ぎ、コード上の命名を統一するために、プロジェクト全体で使用する用語を定義する。

---

## 1. ドメイン用語・ビジネス用語の定義（製造業・業務コンテキスト）

PRD に記載されているターゲットユーザーの業務や対象データに関する用語を定義する。

| 用語 | 定義 |
|---|---|
| **不具合事例** | 量産品・設備において発生した不具合の事象・原因・対処法をまとめた記録。品質管理・生産技術・製品設計のすべてのエンジニアが参照する共通の情報資産 |
| **品質管理** | 量産品の不具合対応・品質改善活動を統括する業務領域。不具合モードの分析、類似事例の調査、再発防止策の策定を含む |
| **生産技術** | 設備の導入・維持・改善に関する技術領域。設備の不具合履歴・技術仕様の調査を担当する |
| **製品設計** | 製品の仕様策定・設計変更を行う技術領域。製品仕様書・設計資料・過去の設計変更履歴を参照する |
| **技術資料（ナレッジベース）** | 社内に蓄積された技術文書の総称。不具合対応履歴、設備仕様書、製品仕様書、設計資料などを含む。本システムの検索対象データソース |
| **未加工データ** | OCR 誤変換、改行混在、フォーマット不統一などクリーニングされていない状態の技術資料。本システムはこの状態のデータも検索・活用できることを要件とする |
| **不具合モード** | 不具合の発生パターンや分類。品質管理エンジニアが過去事例を検索する際の主要な検索軸 |
| **データソース** | ベクトル DB に取り込む元データの総称。初期実装では PDF ファイルを対象とし、将来的に CSV・Excel・Word 等への拡張を想定する |

---

## 2. システム・AI 用語の定義（Agentic RAG コンテキスト）

FD およびアーキテクチャに記載されている、本システム特有の技術用語を定義する。

| 用語 | 定義 |
|---|---|
| **Agentic RAG** | 単純な検索拡張生成（RAG）にとどまらず、AI エージェントが質問の意図を推論し、回答が不十分な場合に自律的に再検索・再推論を繰り返す仕組み。本システムの中核コンセプト |
| **自己修正ループ** | 十分性判定ノード（judge）が情報不足と判断した場合に、追加サブタスクを生成してドキュメント検索ノード（doc_search）へ戻るフィードバックループ。`max_loop_count` で上限を制御する |
| **タスク分割（Task Planning）** | ユーザーの質問を分析し、ナレッジベースを検索するためのサブタスク（目的 + 検索クエリ）に分解する処理。`task_planning` ノードが担当する |
| **サブタスク（Subtask）** | タスク分割によって生成される検索単位。「目的（purpose）」と「検索クエリ（queries）」のペアで構成される |
| **推論過程（Thinking / Reasoning）** | LLM が回答を生成する際の内部的な思考プロセス。Ollama の `reasoning` パラメータで強度（`low` / `medium` / `high`）を制御し、ログとして出力・可視化する |
| **チャンク（Chunk）** | 技術資料から抽出したテキストを、検索に適した短い粒度に分割した単位。ベクトル DB に格納される最小単位 |
| **チャンク分割** | テキストを指定サイズ（`chunk_size`）でオーバーラップ（`chunk_overlap`）を持たせながら分割する処理。短い粒度で分割し、Reranker による精査と組み合わせる戦略を採用 |
| **ハイブリッド検索** | キーワード検索（BM25）とベクトル検索（コサイン類似度）を組み合わせた検索手法。2段階検索戦略の第1段階として、関連チャンクを広く収集する |
| **ベクトル検索** | テキストを Embedding モデルで数値ベクトルに変換し、コサイン類似度で関連文書を検索する手法 |
| **キーワード検索（BM25）** | 単語の出現頻度に基づく伝統的な全文検索手法。ベクトル検索と相補的に機能する |
| **Reranking（リランキング）** | ハイブリッド検索で広く収集した結果を、Reranker モデル（クロスエンコーダ）で再評価・再ランキングし、最終的に回答生成に使用するチャンクを絞り込む処理。2段階検索戦略の第2段階 |
| **Embedding（埋め込み）** | テキストを固定長の数値ベクトルに変換する処理、またはその変換モデル。ベクトル検索の基盤技術 |
| **ハルシネーション** | LLM が検索結果に含まれない情報を、あたかも事実であるかのように生成してしまう現象。システムプロンプトで「検索結果に含まれない情報は含めないでください」と指示することで抑制する |
| **構造化出力（Structured Output）** | LLM に Pydantic モデルの JSON スキーマに準拠した出力を強制する仕組み。LangChain の `with_structured_output()` を使用する |
| **自己修正** | judge ノードが回答の品質を評価し、不十分と判断した場合に追加の検索・推論を自律的に実行するメカニズム |
| **RRF（Reciprocal Rank Fusion）** | キーワード検索とベクトル検索の結果を統合するスコアリング手法。`bm25_weight` パラメータで重み付けを調整する |
| **Port（ポート）** | Clean Architecture における抽象インターフェース。Domain 層で `typing.Protocol` として定義し、外部インフラへの依存を逆転させる |
| **Adapter（アダプタ）** | Port の具体実装。Interface Adapters 層に配置し、外部ライブラリ（Ollama、Chroma DB 等）をドメイン側インターフェースに適合させる |
| **BM25** | 単語の出現頻度と文書長に基づく統計的な全文検索アルゴリズム。ハイブリッド検索の一方の軸として、ベクトル検索と相補的に機能する |
| **コサイン類似度** | 2つのベクトル間の角度に基づく類似度指標（0〜1）。ベクトル検索で文書とクエリの関連度を計算する手法 |
| **クロスエンコーダ** | クエリと候補文書を同時に入力として受け取り、関連度スコアを直接計算するニューラルネットワークモデル。Reranker の実装基盤 |
| **形態素解析** | 日本語テキストを意味のある最小単位（形態素）に分割し、品詞を判定する自然言語処理。BM25 のトークナイズに使用する |
| **推論強度（Reasoning Level）** | Ollama の `reasoning` パラメータで制御する LLM の Thinking の程度。`low` / `medium` / `high` の3段階。ノードの役割に応じて使い分け、トークン消費と精度のバランスを取る |
| **フォールバック** | LLM の構造化出力失敗やタイムアウト発生時に、ワークフローを異常終了させず代替値で処理を継続する仕組み。例：タスク分割失敗時は元の質問をそのまま検索クエリとする |
| **コンテキストウィンドウ** | LLM が一度に処理できる入力トークン数の上限。`llm_num_ctx` で設定する。マルチターンチャットで検索結果が蓄積するとコンテキスト長が増大し、推論品質が低下する場合がある |
| **DI（Dependency Injection / 依存性の注入）** | Port の具体実装（Adapter）をコンストラクタ経由で外部から注入する設計パターン。`DIContainer` が組み立てを担当する |

---

## 3. UI/UX 用語の定義

Gradio を用いた UI 上でユーザーが触れる用語を定義する。

| 用語 | 定義 |
|---|---|
| **システムプロンプト** | LLM の振る舞いを制御するための指示文。Gradio UI 上でユーザーが編集可能。回答生成時にノード固有のシステムプロンプト（`system_prompt_generate_answer`）と結合して LLM に渡される。デフォルトは「日本語で回答してください。」 |
| **Temperature** | LLM の応答の正確さ / 創造性を調整するパラメータ（0.0〜1.0）。低い値ほど確定的（正確）な応答、高い値ほど多様（創造的）な応答を生成する。Gradio UI 上でスライダーとして提供される |
| **思考過程ログ** | AI エージェントの推論ステップ（タスク分割→検索→要約→判定→回答生成）の進行状況をリアルタイムで表示するログ。Gradio UI の左カラムに表示される |
| **マルチターンチャット** | 会話履歴を保持しながら複数ターンの対話を継続する機能。LangGraph のメモリ管理機能で実現し、前のターンの文脈が次の質問に反映される |
| **チャット表示エリア** | ユーザーと AI の会話履歴をスクロール可能な形式で表示する Gradio UI の領域。`gr.Chatbot` コンポーネントで実現 |
| **PDF アップロード** | Gradio UI のファイルアップロード機能を通じて PDF ファイルをシステムに取り込む操作。Google Colab 環境ではローカルディレクトリへの直接アクセスができないため、この方式を採用 |
| **PDF ステータス** | PDF ファイルの取り込み結果（読み込み完了・チャンク数）を表示する UI 領域 |
| **ストリーミング出力** | LLM の回答をトークン単位で逐次的に UI に表示する機能。全体の生成完了を待たずにユーザーが回答を読み始められる。`generate_answer` ノードで `astream` を使用して実現する |
| **セッション状態** | ブラウザタブごとに `gr.State()` で保持されるユーザー固有のデータ（PDF テキスト、スレッド ID など）。Colab ランタイム切断時にはインメモリデータが消失する |
| **会話クリア** | チャット履歴をリセットし、新しい会話セッションを開始する操作 |

---

## 4. 英語・日本語対応表（コード命名規則）

ドメイン設計とコードを一致させる（Domain-Driven Design のアプローチ）ため、上記の用語と Python コード上の命名の厳密な対応表を定義する。

### 4.1 ワークフロー状態（`WorkflowState`）のキー

| 日本語名 | 英語名 / 変数名 | 型 | 適用箇所 |
|---|---|---|---|
| 質問 | `question` | `str` | `WorkflowState` のキー。ユーザーの入力質問文 |
| サブタスク | `subtasks` | `list[dict]` | `WorkflowState` のキー。`{"purpose": str, "queries": [str]}` のリスト |
| 検索結果 | `search_results` | `list[str]` | `WorkflowState` のキー。目的と紐付けた検索結果（生テキスト） |
| 要約 | `summary` | `str` | `WorkflowState` のキー。検索結果の要約テキスト |
| 回答 | `answer` | `str` | `WorkflowState` のキー。最終回答テキスト |
| ループ回数 | `loop_count` | `int` | `WorkflowState` のキー。自己修正ループの現在回数 |

### 4.2 Pydantic モデルのフィールド名

| 日本語名 | 英語名 / 変数名 | 所属モデル | 説明 |
|---|---|---|---|
| 目的 | `purpose` | `Subtask` | サブタスクで明らかにしたいこと |
| 検索クエリ | `queries` | `Subtask` | 検索に使用するクエリのリスト |
| サブタスクリスト | `subtasks` | `TaskPlanningResult` | タスク分割の出力（最大3個） |
| 十分性判定 | `sufficient` | `JudgeResult` | 情報が十分かどうかの真偽値 |
| 判定理由 | `reason` | `JudgeResult` | 判定の理由（日本語で記述） |
| 追加サブタスク | `additional_subtasks` | `JudgeResult` | 不足時に生成される追加のサブタスク |
| メッセージ役割 | `role` | `ChatMessage` | `user` / `assistant` / `system` |
| メッセージ内容 | `content` | `ChatMessage` | メッセージ本文 |
| チャンク ID | `chunk_id` | `DocumentChunk` | チャンクの一意識別子 |
| テキスト | `text` | `DocumentChunk` | チャンクのテキスト内容 |
| ソース | `source` | `DocumentChunk` | 元ファイル名 |
| ページ番号 | `page` | `DocumentChunk` | PDF のページ番号 |
| メタデータ | `metadata` | `DocumentChunk` | 付加情報の辞書 |
| チャンク | `chunk` | `SearchResult` | 検索にヒットした `DocumentChunk` |
| スコア | `score` | `SearchResult` | 類似度または Reranker スコア |

### 4.3 クラス名・モジュール名

| 日本語名 | 英語名 / クラス名 | 適用箇所 |
|---|---|---|
| ワークフロー状態 | `WorkflowState` | `src/usecases/agent_workflow.py` — LangGraph State 定義（`TypedDict`） |
| エージェントワークフロー | `AgentWorkflow` | `src/usecases/agent_workflow.py` — LangGraph グラフの構築・実行 |
| サブタスク | `Subtask` | `src/domain/models.py` — タスク分割の出力単位（Pydantic `BaseModel`） |
| タスク分割結果 | `TaskPlanningResult` | `src/domain/models.py` — タスク分割ノードの出力（Pydantic `BaseModel`） |
| 十分性判定結果 | `JudgeResult` | `src/domain/models.py` — 判定ノードの出力（Pydantic `BaseModel`） |
| チャットメッセージ | `ChatMessage` | `src/domain/models.py` — チャット履歴の1メッセージ |
| ドキュメントチャンク | `DocumentChunk` | `src/domain/models.py` — ベクトル DB に格納するチャンク |
| 検索結果 | `SearchResult` | `src/domain/models.py` — 検索結果（チャンク + スコア） |
| メッセージ役割 | `MessageRole` | `src/domain/models.py` — `Enum`（`USER` / `ASSISTANT` / `SYSTEM`） |
| ワークフロー設定 | `WorkflowConfig` | `src/domain/config.py` — ハイパーパラメータ一元管理（Pydantic `BaseSettings`） |

### 4.4 Port（インターフェース）/ Adapter（具体実装）

| 日本語名 | Port（抽象） | Adapter（具体） | 適用箇所 |
|---|---|---|---|
| LLM クライアント | `LLMPort` | `OllamaAdapter` | `src/domain/ports/llm_port.py` / `src/interfaces/adapters/ollama_adapter.py` |
| ベクトルストア | `VectorStorePort` | `ChromaDBAdapter` | `src/domain/ports/vectorstore_port.py` / `src/interfaces/adapters/chromadb_adapter.py` |
| リランカー | `RerankerPort` | `RerankerAdapter` | `src/domain/ports/reranker_port.py` / `src/interfaces/adapters/reranker_adapter.py` |
| データローダー | `DataLoaderPort` | `PDFLoaderAdapter` | `src/domain/ports/dataloader_port.py` / `src/interfaces/adapters/pdf_loader_adapter.py` |
| DI コンテナ | — | `DIContainer` | `src/infrastructure/di_container.py` |
| データ取り込み | — | `DataIngestion` | `src/usecases/data_ingestion.py` |
| UI ハンドラ | — | `GradioHandler` | `src/interfaces/ui/gradio_handler.py` |

### 4.5 ノード名（LangGraph グラフ）

| 日本語名 | ノード名（グラフキー） | モジュール | 説明 |
|---|---|---|---|
| タスク分割ノード | `task_planning` | `src/usecases/nodes/task_planning_node.py` | 質問をサブタスクに分解 |
| ドキュメント検索ノード | `doc_search` | `src/usecases/nodes/doc_search_node.py` | ハイブリッド検索 + Reranking |
| 検索結果要約ノード | `summarize` | `src/usecases/nodes/summarize_node.py` | 検索結果を圧縮・要約 |
| 十分性判定ノード | `judge` | `src/usecases/nodes/judge_node.py` | 情報の十分性を判定、不足時に追加サブタスク生成 |
| 最終回答生成ノード | `generate_answer` | `src/usecases/nodes/generate_answer_node.py` | 検索結果に基づく回答をストリーミング生成 |

### 4.6 設定パラメータ（`WorkflowConfig` のフィールド名）

| 日本語名 | 変数名 | 説明 |
|---|---|---|
| **ループ制御** | | |
| 最大ループ回数 | `max_loop_count` | 自己修正ループの上限 |
| **LLM 基本パラメータ** | | |
| LLM モデル名 | `llm_model_name` | Ollama で使用する LLM モデル |
| コンテキストウィンドウサイズ | `llm_num_ctx` | LLM のコンテキスト長 |
| Temperature | `llm_temperature` | LLM の応答の多様性制御 |
| Top-K サンプリング | `llm_top_k` | 確率上位 K 個の候補からサンプリング |
| Top-P サンプリング | `llm_top_p` | 累積確率が P に達するまでの候補からサンプリング |
| 繰り返しペナルティ | `llm_repeat_penalty` | 同一トークンの繰り返しを抑制する係数 |
| **ノードごとの推論パラメータ** | | |
| タスク分割の推論強度 | `reasoning_task_planning` | `task_planning` ノードの Thinking 強度（`low` / `medium` / `high`） |
| 要約の推論強度 | `reasoning_summarize` | `summarize` ノードの Thinking 強度 |
| 判定の推論強度 | `reasoning_judge` | `judge` ノードの Thinking 強度 |
| 回答生成の推論強度 | `reasoning_generate_answer` | `generate_answer` ノードの Thinking 強度 |
| **タイムアウト / トークン制限** | | |
| 構造化出力タイムアウト | `structured_output_timeout` | 構造化出力の最大待機時間（秒） |
| 構造化出力最大トークン数 | `structured_output_num_predict` | 構造化出力のトークン上限 |
| 要約タイムアウト | `summarize_timeout` | 要約ノードの最大待機時間（秒） |
| 要約最大トークン数 | `summarize_num_predict` | 要約ノードのトークン上限 |
| **検索パラメータ** | | |
| 検索取得件数 | `retrieval_top_k` | ハイブリッド検索で取得するチャンク数 |
| Reranking 上位件数 | `rerank_top_k` | Reranking 後に残すチャンク数 |
| BM25 重み | `bm25_weight` | RRF におけるキーワード検索の重み |
| 検索結果最大文字数 | `max_return_chars` | 検索結果テキストの最大文字数 |
| **チャンク分割パラメータ** | | |
| チャンクサイズ | `chunk_size` | チャンク分割時の文字数 |
| チャンクオーバーラップ | `chunk_overlap` | チャンク間の重複文字数 |
| ブロック最大バイト数 | `block_max_bytes` | spaCy 分割前のブロック最大バイト数 |
| **モデル選定** | | |
| Embedding モデル名 | `embedding_model_name` | テキストをベクトル化するモデル |
| Reranker モデル名 | `reranker_model_name` | 再ランキングに使用するモデル |
| **システムプロンプト** | | |
| タスク分割プロンプト | `system_prompt_task_planning` | タスク分割ノードの LLM 指示文 |
| 要約プロンプト | `system_prompt_summarize` | 要約ノードの LLM 指示文 |
| 十分性判定プロンプト | `system_prompt_judge` | 十分性判定ノードの LLM 指示文 |
| 回答生成プロンプト | `system_prompt_generate_answer` | 回答生成ノードの LLM 指示文 |
| ユーザーデフォルトプロンプト | `system_prompt_user_default` | Gradio UI でユーザーが編集可能なシステムプロンプトの初期値 |
