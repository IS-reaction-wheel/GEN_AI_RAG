# 初回実装 タスクリスト

## Phase 1: Domain 層（最内層）

- [x] 1-1. `src/domain/models.py` — ドメインモデル + LLM 構造化出力モデルの実装
- [x] 1-2. `src/domain/config.py` — `WorkflowConfig`（Pydantic `BaseSettings`）の実装
- [x] 1-3. `src/domain/ports/llm_port.py` — `ChatResponse` + `LLMPort` の定義
- [x] 1-4. `src/domain/ports/vectorstore_port.py` — `VectorStorePort` の定義
- [x] 1-5. `src/domain/ports/reranker_port.py` — `RerankerPort` の定義
- [x] 1-6. `src/domain/ports/dataloader_port.py` — `DataLoaderPort` の定義
- [x] 1-7. `src/domain/__init__.py`, `src/domain/ports/__init__.py` — パッケージ初期化
- [x] 1-8. `tests/unit/test_models.py` — Pydantic モデルのバリデーションテスト
- [x] 1-9. Ruff フォーマット・リントチェック + コミット

## Phase 2: Use Cases 層

- [x] 2-1. `tests/conftest.py` — 共通モックフィクスチャ（MockLLM, MockVectorStore, MockReranker, MockDataLoader）
- [x] 2-2. `src/usecases/nodes/task_planning_node.py` + `tests/unit/test_task_planning_node.py`
- [x] 2-3. `src/usecases/nodes/doc_search_node.py` + `tests/unit/test_doc_search_node.py`
- [x] 2-4. `src/usecases/nodes/summarize_node.py` + `tests/unit/test_summarize_node.py`
- [x] 2-5. `src/usecases/nodes/judge_node.py` + `tests/unit/test_judge_node.py`
- [x] 2-6. `src/usecases/nodes/generate_answer_node.py`
- [x] 2-7. `src/usecases/agent_workflow.py` — LangGraph グラフ構築 + `WorkflowState`
- [x] 2-8. `src/usecases/data_ingestion.py` + `tests/unit/test_data_ingestion.py`
- [x] 2-9. `src/usecases/__init__.py`, `src/usecases/nodes/__init__.py` — パッケージ初期化
- [x] 2-10. Ruff フォーマット・リントチェック + コミット

## Phase 3: Interface Adapters 層

- [x] 3-1. `src/interfaces/adapters/ollama_adapter.py` — `OllamaAdapter`（`LLMPort` 実装）
- [x] 3-2. `src/interfaces/adapters/chromadb_adapter.py` — `ChromaDBAdapter`（`VectorStorePort` 実装）
- [x] 3-3. `src/interfaces/adapters/reranker_adapter.py` — `RerankerAdapter`（`RerankerPort` 実装）
- [x] 3-4. `src/interfaces/adapters/pdf_loader_adapter.py` — `PDFLoaderAdapter`（`DataLoaderPort` 実装）
- [x] 3-5. `tests/unit/test_data_preprocessing.py` — データ前処理の純粋関数テスト
- [x] 3-6. `src/interfaces/ui/gradio_handler.py` — `GradioHandler`
- [x] 3-7. `src/interfaces/__init__.py`, `src/interfaces/adapters/__init__.py`, `src/interfaces/ui/__init__.py` — パッケージ初期化
- [x] 3-8. Ruff フォーマット・リントチェック + コミット

## Phase 4: Infrastructure 層（最外層）

- [x] 4-1. `src/infrastructure/di_container.py` — `DIContainer`
- [x] 4-2. `src/infrastructure/__init__.py`, `src/__init__.py` — パッケージ初期化
- [x] 4-3. Ruff フォーマット・リントチェック + コミット

## Phase 5: 統合テスト・最終品質チェック

- [x] 5-1. `tests/integration/test_agent_workflow.py` — ワークフロー全体フロー（モック注入）
- [x] 5-2. 全テスト実行（`pytest`）+ Ruff 最終チェック
- [x] 5-3. 依存性のルール遵守を確認（上位層→下位層の直接 import がないこと）
- [x] 5-4. コミット

## Phase 6: Notebook・環境設定

- [x] 6-1. `pyproject.toml` — 依存パッケージの追加
- [x] 6-2. `notebook/` — Google Colab 用 Main ルーチン `.ipynb`
- [ ] 6-3. コミット

---

## 完了条件

- [x] すべてのユニットテスト・統合テストが `pytest` でパスする
- [x] Ruff によるフォーマット・リントエラーがゼロ
- [x] Clean Architecture の依存性のルールが守られている
- [x] すべての関数・メソッドに型ヒントが付与されている
- [x] FD のデータモデル・インターフェース定義と実装コードが一致している
