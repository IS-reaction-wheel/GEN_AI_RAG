# spaCy 辞書を ja_ginza に変更: タスクリスト

## タスク一覧

### コード変更

- [x] `pdf_loader_adapter.py` の `_get_nlp()` で `ja_core_news_sm` → `ja_ginza` に変更
- [x] `notebook/08_Agentic_RAG_Main.ipynb` セル2: pip install に `ginza`, `ja-ginza` を追加
- [x] `notebook/08_Agentic_RAG_Main.ipynb` セル3: `spacy download` → `spacy.load("ja_ginza")` 確認コードに変更

### 永続的ドキュメント更新

- [x] `docs/architecture.md` に spaCy モデル名 `ja_ginza`（GiNZA）を明記

### 品質チェック

- [x] 既存テスト 39 件パス
- [x] Ruff チェッククリーン
