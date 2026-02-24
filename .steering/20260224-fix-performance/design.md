# 性能改善: 設計

## 実装アプローチ

### D1: spaCy モデルキャッシュ（tokenize 性能修正）

**問題の根本原因:**
`pdf_loader_adapter.py` の `tokenize()` 関数内で毎回 `spacy.load("ja_core_news_sm")` を呼んでいた。BM25 インデックス構築時に全チャンク分（例: 214回）モデルロードが発生し、PDF 読み込みが極端に遅くなっていた。

**修正方針:**
モジュールレベルのシングルトンパターンでキャッシュする。

```python
_nlp_instance = None

def _get_nlp():
    global _nlp_instance
    if _nlp_instance is None:
        import spacy
        _nlp_instance = spacy.load("ja_core_news_sm", disable=["parser", "ner"])
    return _nlp_instance

def tokenize(text: str) -> list[str]:
    nlp = _get_nlp()
    ...
```

- `disable=["parser", "ner"]` で不要なパイプラインを無効化し、さらに高速化
- モデルが見つからない場合は `text.split()` にフォールバック

### D2: GradioHandler ストリーミング対応

**問題の根本原因:**
GradioHandler.respond() が `AgentWorkflow.ainvoke(state)` を1回呼ぶだけの構造だった。LangGraph のワークフロー内部で全ノードが順次実行されるため、完了まで UI が無反応になっていた。

**修正方針:**
notebook 07 と同様に、各ノードのファクトリ関数から生成したノード関数を GradioHandler 内で個別に呼び出す。

**変更するコンポーネント:**

1. **GradioHandler.__init__()** — LLM・VectorStore・Reranker の Port を直接受け取り、ノードファクトリから各ノード関数を生成・保持する
2. **GradioHandler.respond()** — 各ノードを個別に呼び出し、フェーズごとに `yield` で思考ログを返す。最終回答は `llm.astream()` でトークン単位ストリーミング
3. **DIContainer.create_ui()** — GradioHandler に LLM・VectorStore・Reranker を渡すように変更

**respond() のフロー:**
```
Phase 1: task_planning(state) → yield 思考ログ
Phase 2: ループ
  doc_search(state)   → yield 思考ログ
  summarize(state)    → yield 思考ログ
  judge(state)        → yield 思考ログ（不足なら再ループ）
Phase 3: llm.astream() → yield トークン単位ストリーミング
```

## 変更するコンポーネント

| ファイル | 変更内容 |
|---|---|
| `src/interfaces/adapters/pdf_loader_adapter.py` | `tokenize()` に spaCy モデルキャッシュ追加 |
| `src/interfaces/ui/gradio_handler.py` | respond() をステップ実行 + ストリーミングに全面書き換え |
| `src/infrastructure/di_container.py` | create_ui() が LLM・VectorStore・Reranker を渡すよう変更 |

## 影響範囲の分析

- **AgentWorkflow** — 変更なし。GradioHandler が直接使わなくなるだけで、クラス自体は維持
- **各ノードファクトリ** — 変更なし。既存の `create_*_node()` をそのまま利用
- **DIContainer** — create_ui() のシグネチャ変更のみ。他の create_* メソッドは影響なし
- **テスト** — 既存 39 テストに影響なし（GradioHandler のテストは未作成）
