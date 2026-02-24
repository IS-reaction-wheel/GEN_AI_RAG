# 性能改善: タスクリスト

## タスク一覧

### D1: spaCy モデルキャッシュ

- [x] `pdf_loader_adapter.py` にモジュールレベルの `_nlp_instance` と `_get_nlp()` を追加
- [x] `tokenize()` を `_get_nlp()` 経由に変更し、`disable=["parser", "ner"]` を適用
- [x] モデル未インストール時のフォールバック（`text.split()`）を維持

### D2: GradioHandler ストリーミング対応

- [x] `GradioHandler.__init__()` — LLM・VectorStore・Reranker Port を受け取り、ノードファクトリで各ノード関数を生成
- [x] `GradioHandler.respond()` — 各ノード個別呼び出し + フェーズごとの yield + llm.astream() トークンストリーミング
- [x] `GradioHandler.launch()` — 停止ボタン追加、notebook 07 準拠の UI レイアウト
- [x] `DIContainer.create_ui()` — LLM・VectorStore・Reranker を GradioHandler に渡すよう変更

### 品質チェック

- [x] 既存テスト 39 件パス
- [x] Ruff チェッククリーン
