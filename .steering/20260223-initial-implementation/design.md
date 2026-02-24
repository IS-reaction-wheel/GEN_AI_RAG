# 初回実装 設計書

## 1. 実装アプローチ

FD（機能設計書）で定義されたクラス設計・インターフェース・ワークフロー設計をそのまま実装コードに落とし込む。開発ガイドライン（5.1 ステップバイステップの実装）に従い、内側の層（Domain）から外側の層（Infrastructure）へ順に実装する。

### 実装順序

```
Phase 1: Domain 層（最内層）
  1-1. models.py — ドメインモデル + LLM 構造化出力モデル
  1-2. config.py — WorkflowConfig（ハイパーパラメータ）
  1-3. ports/ — 4つの Port（Protocol）定義
  → テスト: test_models.py
  → コミット

Phase 2: Use Cases 層
  2-1. nodes/task_planning_node.py
  2-2. nodes/doc_search_node.py
  2-3. nodes/summarize_node.py
  2-4. nodes/judge_node.py
  2-5. nodes/generate_answer_node.py
  2-6. agent_workflow.py — LangGraph グラフ構築
  2-7. data_ingestion.py — データ取り込みユースケース
  → テスト: 各ノードのユニットテスト + conftest.py
  → コミット（ノード単位）

Phase 3: Interface Adapters 層
  3-1. adapters/ollama_adapter.py
  3-2. adapters/chromadb_adapter.py
  3-3. adapters/reranker_adapter.py
  3-4. adapters/pdf_loader_adapter.py
  3-5. ui/gradio_handler.py
  → テスト: test_data_preprocessing.py
  → コミット（アダプタ単位）

Phase 4: Infrastructure 層（最外層）
  4-1. di_container.py — DI コンテナ
  → コミット

Phase 5: テスト・品質チェック
  5-1. 統合テスト（test_agent_workflow.py）
  5-2. Ruff フォーマット・リントチェック
  → コミット

Phase 6: Notebook
  6-1. Google Colab 用 Main ルーチン .ipynb
  → コミット
```

---

## 2. 変更するコンポーネント（新規作成）

### 2.1 ディレクトリ構造（新規作成ファイル一覧）

```
src/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   └── ports/
│       ├── __init__.py
│       ├── llm_port.py
│       ├── vectorstore_port.py
│       ├── reranker_port.py
│       └── dataloader_port.py
├── usecases/
│   ├── __init__.py
│   ├── agent_workflow.py
│   ├── data_ingestion.py
│   └── nodes/
│       ├── __init__.py
│       ├── task_planning_node.py
│       ├── doc_search_node.py
│       ├── summarize_node.py
│       ├── judge_node.py
│       └── generate_answer_node.py
├── interfaces/
│   ├── __init__.py
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── ollama_adapter.py
│   │   ├── chromadb_adapter.py
│   │   ├── reranker_adapter.py
│   │   └── pdf_loader_adapter.py
│   └── ui/
│       ├── __init__.py
│       └── gradio_handler.py
└── infrastructure/
    ├── __init__.py
    └── di_container.py

tests/
├── conftest.py
├── unit/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_data_preprocessing.py
│   ├── test_task_planning_node.py
│   ├── test_doc_search_node.py
│   ├── test_summarize_node.py
│   ├── test_judge_node.py
│   └── test_data_ingestion.py
└── integration/
    ├── __init__.py
    └── test_agent_workflow.py
```

---

## 3. 各コンポーネントの設計詳細

### 3.1 Domain 層

#### `models.py`

FD セクション 5.2〜5.3 の定義をそのまま実装する。

- `MessageRole`（`str, Enum`）: `USER`, `ASSISTANT`, `SYSTEM`
- `ChatMessage`（`BaseModel`, `frozen=True`）: `role`, `content`
- `DocumentChunk`（`BaseModel`, `frozen=True`）: `chunk_id`, `text`, `source`, `page`, `metadata`
- `SearchResult`（`BaseModel`, `frozen=True`）: `chunk`, `score`
- `Subtask`（`BaseModel`）: `purpose`, `queries`
- `TaskPlanningResult`（`BaseModel`）: `subtasks`
- `JudgeResult`（`BaseModel`）: `sufficient`, `reason`, `additional_subtasks` + `@model_validator`

#### `config.py`

FD セクション 4.2 の `WorkflowConfig` をそのまま実装する。システムプロンプトのデフォルト値は FD セクション 4.3 から取得する。

#### `ports/`

FD セクション 10.1〜10.4 の Protocol 定義をそのまま実装する。

- `llm_port.py`: `ChatResponse` + `LLMPort`（`agenerate`, `agenerate_structured`, `astream`）
- `vectorstore_port.py`: `VectorStorePort`（`add_documents`, `similarity_search`, `keyword_search`）
- `reranker_port.py`: `RerankerPort`（`rerank`）
- `dataloader_port.py`: `DataLoaderPort`（`load`）

### 3.2 Use Cases 層

#### ノード群

FD セクション 11 の詳細設計に基づいて実装する。各ノードは関数として定義し、Port をクロージャまたはクラスで保持する。

**ノード関数のシグネチャ設計:**

各ノード関数は LangGraph のノードとして `WorkflowState` を受け取り、状態の更新分を `dict` で返す。Port への依存は、ノード関数を生成するファクトリ関数（またはクラス）を通じて注入する。

```python
# ノードファクトリパターン（各ノードで採用）
def create_task_planning_node(
    llm: LLMPort,
    config: WorkflowConfig,
) -> Callable[[WorkflowState], Awaitable[dict]]:
    async def task_planning_node(state: WorkflowState) -> dict:
        ...
    return task_planning_node
```

**各ノードの実装方針:**

| ノード | LLM 呼び出し | エラーハンドリング |
|---|---|---|
| `task_planning` | `agenerate_structured(TaskPlanningResult)` | タイムアウト / バリデーション失敗 → フォールバック（元の質問をクエリとする） |
| `doc_search` | なし（VectorStore + Reranker） | 検索結果0件 → 空リストで継続 |
| `summarize` | `agenerate()` テキスト生成 | タイムアウト → 検索結果をそのまま使用 |
| `judge` | `agenerate_structured(JudgeResult)` | タイムアウト / バリデーション失敗 → sufficient=True で回答生成へ |
| `generate_answer` | `astream()` ストリーミング | ストリーミング中断 → その時点のテキストを回答とする |

#### `agent_workflow.py`

FD セクション 11.3 の LangGraph グラフ構造を実装する。

- `WorkflowState`（`TypedDict`）
- `AgentWorkflow` クラス: Port と Config を受け取り、グラフを構築
- `should_continue` 条件分岐関数
- マルチターンチャット用の `MemorySaver` チェックポインター

#### `data_ingestion.py`

- `DataIngestion` クラス: `DataLoaderPort` と `VectorStorePort` を受け取る
- `ingest(file_path: str) -> int`: ファイルからチャンクを生成し DB に格納、件数を返す

### 3.3 Interface Adapters 層

#### `ollama_adapter.py`

- LangChain の `ChatOllama` をラップ
- `_make_llm()` で `num_predict` / `reasoning` をオーバーライドした LLM インスタンスを生成
- `_to_langchain_messages()` で `list[dict]` → LangChain メッセージに変換
- `agenerate_structured()` 内で `with_structured_output()` を使用

#### `chromadb_adapter.py`

- Chroma DB のインメモリコレクションを管理
- `add_documents()`: Embedding 関数でベクトル化して格納
- `similarity_search()`: コサイン類似度検索
- `keyword_search()`: rank_bm25 の `BM25Okapi` + spaCy トークナイズ
- BM25 インデックスはドキュメント追加時に再構築

#### `reranker_adapter.py`

- Sentence Transformers の `CrossEncoder` をラップ
- `rerank()`: クエリと候補チャンクのペアをスコアリングし、上位 `top_k` を返す

#### `pdf_loader_adapter.py`

- markitdown で PDF → Markdown 変換
- テキストクリーニング（`clean_pdf_text`）: 1文字行ブロック除去、連続空行圧縮
- spaCy のバイト制限対策ブロック分割（`split_into_safe_blocks`）
- spaCy `ja_core_news_sm` による形態素解析チャンク分割
- BM25 用トークナイズ関数（`tokenize`）

**公開関数（テスト対象）:**

| 関数 | 役割 |
|---|---|
| `clean_pdf_text(text: str) -> str` | PDF テキストのノイズ除去 |
| `split_into_safe_blocks(text: str, max_bytes: int, overlap_chars: int) -> list[str]` | spaCy バイト制限対策の段落分割 |
| `tokenize(text: str) -> list[str]` | BM25 用形態素解析トークナイズ |

#### `gradio_handler.py`

FD セクション 9 の画面設計に基づいて実装する。

- 左右2カラムレイアウト
- `gr.State()` によるセッション管理
- ストリーミング回答表示（`yield` ベース）
- 思考過程のリアルタイム表示
- PDF アップロードと取り込み

### 3.4 Infrastructure 層

#### `di_container.py`

FD セクション 4.4 / 6.3 の設計に基づく。

- `WorkflowConfig` を受け取り、すべてのアダプタとユースケースを組み立て
- コンストラクタインジェクションで依存を注入
- ファクトリメソッド: `create_workflow()`, `create_ingestion()`, `create_ui()`

---

## 4. 依存パッケージの追加

`pyproject.toml` の `dependencies` に以下を追加する必要がある。

| パッケージ | 用途 |
|---|---|
| `pydantic` | ドメインモデル・構造化出力 |
| `pydantic-settings` | `WorkflowConfig`（`BaseSettings`） |
| `langchain-ollama` | Ollama LLM アダプタ（`ChatOllama`） |
| `langgraph` | ワークフローグラフ |
| `chromadb` | ベクトル DB |
| `sentence-transformers` | Embedding / Reranker |
| `rank-bm25` | BM25 キーワード検索 |
| `markitdown` | PDF → Markdown 変換 |
| `spacy` | 形態素解析・チャンク分割 |
| `gradio` | Web UI |

dev 依存（既存の `pytest`, `jupyter` に加え）:

| パッケージ | 用途 |
|---|---|
| `ruff` | フォーマッター / リンター |

---

## 5. 影響範囲の分析

### 5.1 永続的ドキュメントへの影響

初回実装のため、FD で定義された設計をそのまま実装する。永続的ドキュメントの更新は不要。

### 5.2 リスクと対策

| リスク | 対策 |
|---|---|
| FD の概念コードと実際の LangChain / LangGraph API の差異 | FD の設計意図を維持しつつ、実際の API に合わせて調整。設計変更が必要な場合は承認を得る |
| spaCy 日本語モデルが開発環境にインストールされていない | テストでは spaCy 依存の関数はモック可能な設計とする。Colab 実行時にモデルをダウンロード |
| Google Colab と開発環境（Windows）のパス差異 | パス操作には `pathlib.Path` を使用し、OS 依存を最小化 |
