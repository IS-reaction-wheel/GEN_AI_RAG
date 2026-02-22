# リポジトリ構造定義書（Repository Structure）

## 1. フォルダ・ファイル構成（全体ツリー）

```
GEN_AI_RAG/
├── app/                        # Gradio UI のエントリーポイント用スクリプト
├── data/                       # RAG で読み込むテストデータ（PDF）※GitHub 未アップロード
├── docs/                       # 永続的ドキュメント（設計書・仕様書）
├── notebook/                   # 各実装要素の確認用 Jupyter Notebook（Ollama ベース）
│   ├── images/                 # デモ GIF・スクリーンショット等
│   └── outputs/                # Notebook 出力（チャットログ・推論ログ等）
├── notebook_transformers/      # 初期の transformers ベース実装（アーカイブ）
├── outputs/                    # ファイル出力
├── prompts_SDD/                # 仕様駆動開発のドキュメント作成指示プロンプト
├── scripts/                    # 前処理・モデルチューニング等のスクリプト
├── src/                        # 主要な実装コード（Clean Architecture）
├── tests/                      # 単体テスト・統合テストコード
├── .steering/                  # 作業単位の一時的なステアリングファイル
├── .env                        # 環境変数設定 ※GitHub 未アップロード
├── CLAUDE.md                   # Claude Code 向けの開発ルールとプロジェクトメモリ
├── README.md                   # リポジトリの概要・環境・参考文献
├── pyproject.toml              # Python プロジェクト設定
└── uv.lock                     # 依存パッケージのロックファイル
```

### 各ディレクトリの役割

| ディレクトリ | 役割 |
|---|---|
| `app/` | Gradio UI のエントリーポイント。DIContainer で初期化し、Gradio UI を起動するスクリプトを配置 |
| `data/` | RAG で読み込むテストデータ（PDF）を格納。機密情報を含むため GitHub には未アップロード |
| `docs/` | アプリケーション全体の設計を定義する永続的ドキュメント群を配置（詳細はセクション 3 参照） |
| `notebook/` | Google Colab 上で実行する Main ルーチン（`.ipynb`）を配置。`src/` のモジュールを import して使用する |
| `notebook_transformers/` | 初期の transformers ベース実装のアーカイブ。Ollama ベースに移行後は参照用として保持 |
| `outputs/` | スクリプトやワークフローのファイル出力先 |
| `prompts_SDD/` | 仕様駆動開発（SDD）におけるドキュメント作成指示プロンプトを格納 |
| `scripts/` | 前処理やモデルチューニングなど、パラメータ調整が必要なコードを配置 |
| `src/` | Clean Architecture に基づく主要な実装コード（詳細はセクション 2 参照） |
| `tests/` | ユニットテスト・統合テストコードを配置（詳細はセクション 4 参照） |
| `.steering/` | 特定の開発作業における一時的なステアリングファイルを配置（詳細はセクション 3 参照） |

### ルート直下の主要ファイル

| ファイル | 役割 |
|---|---|
| `README.md` | リポジトリの概要、環境構成、フォルダ構成、参考文献などを記載 |
| `CLAUDE.md` | Claude Code 向けのプロジェクトメモリ。開発ルール・ドキュメント分類・開発プロセスを定義 |
| `.env` | 環境変数設定ファイル。`WorkflowConfig`（Pydantic `BaseSettings`）が `RAG_` プレフィックスで読み込む。GitHub には未アップロード |
| `pyproject.toml` | Python プロジェクトの設定（依存パッケージ等） |
| `uv.lock` | `uv` パッケージマネージャによる依存パッケージのロックファイル |

---

## 2. `src/` 配下の詳細構造（Clean Architecture）

機能設計書（FD）で定義された Clean Architecture に基づき、`src/` ディレクトリを4つの層に分割する。上位層（Domain / Use Cases）は下位層（Infrastructure / Frameworks）に直接依存せず、Port（`typing.Protocol`）を介して依存性を逆転させる。

```
src/
├── domain/                     # Domain 層（最内層）
│   ├── __init__.py
│   ├── config.py               # ハイパーパラメータ設定（WorkflowConfig）
│   ├── models.py               # ドメインモデル（ChatMessage, SearchResult 等）
│   └── ports/                  # インターフェース定義（Port）
│       ├── __init__.py
│       ├── llm_port.py         # LLM クライアントのインターフェース
│       ├── vectorstore_port.py # ベクトルストアのインターフェース
│       ├── reranker_port.py    # Reranker のインターフェース
│       └── dataloader_port.py  # データローダーのインターフェース
│
├── usecases/                   # Use Cases 層
│   ├── __init__.py
│   ├── agent_workflow.py       # LangGraph ワークフローグラフ定義
│   ├── nodes/                  # エージェントノード群
│   │   ├── __init__.py
│   │   ├── task_planning_node.py  # タスク分割ノード（サブタスク・検索クエリ生成）
│   │   ├── doc_search_node.py     # ドキュメント検索ノード（ハイブリッド検索 + Reranking）
│   │   ├── summarize_node.py      # 検索結果要約ノード
│   │   ├── judge_node.py          # 十分性判定ノード（自己修正判定）
│   │   └── generate_answer_node.py  # 最終回答生成ノード
│   └── data_ingestion.py      # データ取り込みユースケース
│
├── interfaces/                 # Interface Adapters 層
│   ├── __init__.py
│   ├── adapters/               # インフラアダプタ（Port の実装）
│   │   ├── __init__.py
│   │   ├── ollama_adapter.py   # Ollama LLM アダプタ（LLMPort の実装）
│   │   ├── chromadb_adapter.py # Chroma DB アダプタ（VectorStorePort の実装、Embedding 処理を内包）
│   │   ├── reranker_adapter.py # Sentence Transformers Reranker アダプタ（RerankerPort の実装）
│   │   └── pdf_loader_adapter.py  # PDF データローダーアダプタ（DataLoaderPort の実装）
│   └── ui/                     # UI ハンドラ
│       ├── __init__.py
│       └── gradio_handler.py   # Gradio UI ハンドラ（チャット・ファイルアップロード）
│
└── infrastructure/             # Infrastructure 層（最外層）
    ├── __init__.py
    └── di_container.py         # DI コンテナ（依存性の組み立て・注入）
```

### 各層の役割と配置ルール

#### Domain 層（`src/domain/`）— 最内層

| 配置するもの | 説明 |
|---|---|
| ドメインモデル（`models.py`） | Pydantic `BaseModel` によるデータクラス（`ChatMessage`, `DocumentChunk`, `SearchResult` 等）および LLM 構造化出力用モデル（`TaskPlanningResult`, `JudgeResult` 等） |
| Port（`ports/`） | `typing.Protocol` によるインターフェース定義（`LLMPort`, `VectorStorePort`, `RerankerPort`, `DataLoaderPort`）。外部インフラの具体的な実装詳細を一切含まない |
| ハイパーパラメータ設定（`config.py`） | Pydantic `BaseSettings` による `WorkflowConfig`。LLM パラメータ・検索パラメータ・チャンク分割設定・システムプロンプトを一元管理 |

**ルール**: Domain 層は他のどの層にも依存しない。外部ライブラリのインポートは Pydantic 等の汎用ライブラリに限定する。

#### Use Cases 層（`src/usecases/`）

| 配置するもの | 説明 |
|---|---|
| ワークフロー定義（`agent_workflow.py`） | LangGraph による Agentic RAG ワークフローグラフの構築。`StateGraph` の定義と条件分岐ロジックを含む |
| エージェントノード群（`nodes/`） | 各ノード（タスク分割・検索・要約・判定・回答生成）のビジネスロジック。Port にのみ依存し、具体的なインフラ実装を知らない |
| データ取り込み（`data_ingestion.py`） | PDF → チャンク分割 → ベクトル DB 格納のユースケース。`DataLoaderPort` と `VectorStorePort` に依存 |

**ルール**: Use Cases 層は Domain 層の Port にのみ依存する。Interface Adapters 層や Infrastructure 層を直接参照してはならない。

#### Interface Adapters 層（`src/interfaces/`）

| 配置するもの | 説明 |
|---|---|
| アダプタ群（`adapters/`） | Domain 層の Port を実装する具体的なアダプタ。外部ライブラリ（Ollama, Chroma DB, Sentence Transformers 等）の呼び出しをカプセル化する。Embedding モデル（Sentence Transformers）は独立した Port を持たず、`ChromaDBAdapter` の内部依存として `embedding_fn` を DI コンテナから注入される設計 |
| UI ハンドラ（`ui/`） | Gradio UI のイベントハンドリング。Use Cases 層のワークフローを呼び出してユーザーとのインタラクションを仲介する |

**ルール**: アダプタは対応する Port のプロトコルに準拠して実装する。新しいデータソース（CSV, Excel 等）に対応する場合は、`DataLoaderPort` を実装する新しいアダプタを `adapters/` に追加する。

#### Infrastructure 層（`src/infrastructure/`）— 最外層

| 配置するもの | 説明 |
|---|---|
| DI コンテナ（`di_container.py`） | すべての依存性を組み立て、コンストラクタインジェクションで各コンポーネントに注入する。`WorkflowConfig` を受け取り、Adapter のインスタンス化とワークフローの構築を行う |

**ルール**: DI コンテナはすべての層を参照できる唯一のコンポーネント。アプリケーションの組み立て（Composition Root）としてのみ機能する。

---

## 3. ドキュメントとタスク管理の構造（仕様駆動開発）

本プロジェクトは仕様駆動開発（SDD）を採用し、`CLAUDE.md` を起点としてドキュメントとコードを管理する。ドキュメントは「永続的ドキュメント」と「作業単位のドキュメント」に分類される。

### 3.1 永続的ドキュメント（`docs/`）

アプリケーション全体の「**何を作るか**」「**どう作るか**」を定義する恒久的なドキュメント群。アプリケーションの基本設計や方針が変わらない限り更新されない。プロジェクト全体の「北極星」として機能する。

```
docs/
├── product-requirements.md     # プロダクト要求定義書（PRD）
├── functional-design.md        # 機能設計書（FD）
├── architecture.md             # 技術仕様書
├── repository-structure.md     # リポジトリ構造定義書（本ドキュメント）
├── development-guidelines.md   # 開発ガイドライン
└── glossary.md                 # ユビキタス言語定義
```

| ドキュメント | 内容 |
|---|---|
| `product-requirements.md` | プロダクトビジョン、ターゲットユーザー、機能要件、非機能要件、ユーザーストーリー |
| `functional-design.md` | アーキテクチャ設計、ディレクトリ構成、データモデル、コンポーネント設計、ワークフロー設計、画面設計 |
| `architecture.md` | テクノロジースタック、開発ツール、技術的制約、パフォーマンス要件 |
| `repository-structure.md` | フォルダ・ファイル構成、ディレクトリの役割、ファイル配置ルール |
| `development-guidelines.md` | コーディング規約、命名規則、テスト規約、Git 規約 |
| `glossary.md` | ドメイン用語・ビジネス用語の定義、英語・日本語対応表 |

**配置ルール**: 設計図やダイアグラム（ER 図、ユースケース図、ワイヤフレーム等）は関連するドキュメント内に Mermaid 記法または ASCII アートで直接記載する。独立した `diagrams/` フォルダは作成しない。画像ファイルが必要な場合のみ `docs/images/` に配置する。

### 3.2 作業単位のドキュメント（`.steering/`）

特定の開発作業における「**今回何をするか**」を定義する一時的なステアリングファイル。作業完了後は履歴として保持され、新しい作業では新しいディレクトリを作成する。

```
.steering/
├── [YYYYMMDD]-[開発タイトル]/
│   ├── requirements.md         # 今回の作業の要求内容
│   ├── design.md               # 変更内容の設計
│   └── tasklist.md             # タスクリストと進捗状況
└── ...
```

#### 命名規則

```
.steering/[YYYYMMDD]-[開発タイトル]/
```

**例:**
- `.steering/20250103-initial-implementation/`
- `.steering/20250115-add-tag-feature/`
- `.steering/20250120-fix-filter-bug/`

#### 各ドキュメントの役割

| ドキュメント | 内容 |
|---|---|
| `requirements.md` | 変更・追加する機能の説明、ユーザーストーリー、受け入れ条件、制約事項 |
| `design.md` | 実装アプローチ、変更するコンポーネント、データ構造の変更、影響範囲の分析 |
| `tasklist.md` | 具体的な実装タスク、タスクの進捗状況、完了条件 |

---

## 4. ファイル配置と命名ルール

### 4.1 Python モジュール（`src/` 配下）

#### 命名規則

- **ファイル名**: スネークケース（`snake_case.py`）を使用する
  - 例: `agent_workflow.py`, `ollama_adapter.py`, `pdf_loader_adapter.py`
- **クラス名**: パスカルケース（`PascalCase`）を使用する
  - 例: `AgentWorkflow`, `OllamaAdapter`, `WorkflowConfig`
- **関数名・変数名**: スネークケース（`snake_case`）を使用する
- **定数**: アッパースネークケース（`UPPER_SNAKE_CASE`）を使用する

#### 配置ルール（DI の原則に基づく）

| ルール | 説明 |
|---|---|
| **層をまたいだ直接参照の禁止** | Use Cases 層から Interface Adapters 層のモジュールを直接 import してはならない。必ず Domain 層の Port を介して依存する |
| **依存の方向は内側のみ** | 外側の層は内側の層に依存できるが、内側の層が外側の層に依存してはならない（依存性のルール） |
| **Port と Adapter の対応** | 1つの Port に対して1つ以上の Adapter を実装する。Adapter のファイル名は `[技術名]_adapter.py` とする |
| **ノードの配置** | エージェントノードは `src/usecases/nodes/` 配下に `[ノード名]_node.py` として配置する |
| **`__init__.py` の配置** | すべてのパッケージディレクトリに `__init__.py` を配置する |

### 4.2 Notebook（`notebook/` 配下）

#### 命名・配置ルール

- **Main ルーチン**: Google Colab 上で実行する Jupyter Notebook（`.ipynb`）形式で実装する
- **役割**: DIContainer による初期化と Gradio UI の起動を Notebook セル内で行い、`src/` 配下のモジュールを import して使用する
- **付随ファイル**: デモ用画像は `notebook/images/`、出力ログは `notebook/outputs/` に配置する

### 4.3 テストコード（`tests/` 配下）

#### ディレクトリ構造

`tests/` はテストの性質（実行速度・外部依存の有無）に基づいてディレクトリを分類する。この構成は pytest のマーカーや CI/CD パイプラインでのテスト実行制御と親和性が高い。

```
tests/
├── unit/                          # ユニットテスト（外部依存なし / モック使用、高速）
│   ├── test_models.py             # Pydantic モデルのバリデーションテスト
│   ├── test_data_preprocessing.py # データ前処理（純粋関数）のテスト
│   ├── test_task_planning_node.py # タスク分割ノードのテスト（モック注入）
│   ├── test_doc_search_node.py    # ドキュメント検索ノードのテスト（モック注入）
│   ├── test_summarize_node.py     # 要約ノードのテスト（モック注入）
│   ├── test_judge_node.py         # 判定ノードのテスト（モック注入）
│   └── test_data_ingestion.py     # データ取り込みユースケースのテスト（モック注入）
├── integration/                   # 統合テスト（実ライブラリ使用、低速）
│   ├── test_ingestion_pipeline.py # データ取り込みパイプライン全体
│   └── test_agent_workflow.py     # AgentWorkflow 全体フロー（モック注入）
└── conftest.py                    # 共通フィクスチャ（モック定義等）
```

#### ファイル命名規則

- **テストファイル**: `test_[対象モジュール名].py`（`test_` プレフィックス必須）
  - 例: `test_models.py`, `test_agent_workflow.py`, `test_pdf_loader_adapter.py`
- **テストクラス**: `Test[対象クラス名]`
  - 例: `TestJudgeResult`, `TestCleanPdfText`
- **テスト関数**: `test_[テスト内容を説明する名前]`
  - 例: `test_judge_result_force_consistency_no_additional_subtasks`
