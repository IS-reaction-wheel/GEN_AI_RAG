# 初回実装 要求定義

## 1. 概要

永続的ドキュメント（`docs/`）で定義された Agentic RAG システムの全機能を初回実装する。Clean Architecture に基づく4層構造（Domain / Use Cases / Interface Adapters / Infrastructure）でモジュールを構築し、Google Colab 上での動作を前提とする。

---

## 2. 実装スコープ

### 2.1 Domain 層

- **ドメインモデル**（`src/domain/models.py`）
  - `MessageRole`, `ChatMessage`, `DocumentChunk`, `SearchResult`
  - `Subtask`, `TaskPlanningResult`, `JudgeResult`（`@model_validator` 含む）
- **ハイパーパラメータ設定**（`src/domain/config.py`）
  - `WorkflowConfig`（Pydantic `BaseSettings`）
- **Port（インターフェース）定義**（`src/domain/ports/`）
  - `LLMPort`（`ChatResponse` 含む）
  - `VectorStorePort`
  - `RerankerPort`
  - `DataLoaderPort`

### 2.2 Use Cases 層

- **エージェントノード群**（`src/usecases/nodes/`）
  - `task_planning_node.py` — タスク分割（構造化出力）
  - `doc_search_node.py` — ハイブリッド検索 + Reranking
  - `summarize_node.py` — 検索結果要約
  - `judge_node.py` — 十分性判定（構造化出力 + 自己修正ループ）
  - `generate_answer_node.py` — 最終回答生成（ストリーミング）
- **ワークフロー定義**（`src/usecases/agent_workflow.py`）
  - LangGraph `StateGraph` によるグラフ構築
  - `WorkflowState`（`TypedDict`）
  - 条件分岐（`should_continue`）
- **データ取り込み**（`src/usecases/data_ingestion.py`）
  - `DataIngestion` クラス

### 2.3 Interface Adapters 層

- **アダプタ群**（`src/interfaces/adapters/`）
  - `ollama_adapter.py` — `LLMPort` の実装（LangChain `ChatOllama`）
  - `chromadb_adapter.py` — `VectorStorePort` の実装（Chroma DB + BM25）
  - `reranker_adapter.py` — `RerankerPort` の実装（Sentence Transformers）
  - `pdf_loader_adapter.py` — `DataLoaderPort` の実装（markitdown + spaCy）
- **UI ハンドラ**（`src/interfaces/ui/gradio_handler.py`）
  - `GradioHandler` クラス（チャット・ファイルアップロード・思考過程表示）

### 2.4 Infrastructure 層

- **DI コンテナ**（`src/infrastructure/di_container.py`）
  - `DIContainer` クラス（全依存性の組み立て・注入）

### 2.5 テスト

- **ユニットテスト**（`tests/unit/`）
  - `test_models.py` — Pydantic モデルのバリデーション
  - `test_data_preprocessing.py` — データ前処理の純粋関数
  - `test_task_planning_node.py` — タスク分割ノード（モック注入）
  - `test_doc_search_node.py` — ドキュメント検索ノード（モック注入）
  - `test_summarize_node.py` — 要約ノード（モック注入）
  - `test_judge_node.py` — 判定ノード（モック注入）
  - `test_data_ingestion.py` — データ取り込み（モック注入）
- **統合テスト**（`tests/integration/`）
  - `test_agent_workflow.py` — ワークフロー全体フロー（モック注入）
- **共通フィクスチャ**（`tests/conftest.py`）

### 2.6 Notebook（Main ルーチン）

- `notebook/` 配下に Google Colab 用の `.ipynb` を配置
- DIContainer による初期化と Gradio UI の起動

---

## 3. 受け入れ条件

| # | 条件 |
|---|---|
| AC-01 | `src/` 配下のモジュールが Clean Architecture の依存性のルールに従い、上位層から下位層への直接依存がない |
| AC-02 | すべての関数・メソッドに型ヒントが付与されている |
| AC-03 | Pydantic モデルの `@model_validator` が正しく動作し、テストで検証されている |
| AC-04 | Port のモックを注入したユニットテストが `pytest` で全件パスする |
| AC-05 | Ruff によるフォーマット・リントエラーがない |
| AC-06 | 各ノードのエラーハンドリング（タイムアウト・バリデーション失敗）がフォールバック値で処理を継続する |
| AC-07 | `WorkflowConfig` でハイパーパラメータが一元管理され、DI コンテナ経由で注入される |

---

## 4. 制約事項

- 開発環境は Windows 11 / VS Code / Claude Code。実行環境は Google Colab
- 外部パッケージの追加は `pyproject.toml` に記載されているもののみ使用する
- FD で定義されたデータモデル・インターフェースに準拠する
- 1コンポーネントずつ段階的に実装し、各段階で品質チェックを行う
