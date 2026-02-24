# 検索品質の修正: タスクリスト

## タスク一覧

### コード変更

- [x] `di_container.py`: embedding 関数を document 用 / query 用に分離
- [x] `chromadb_adapter.py`: コンストラクタで2つの embedding 関数を受取 + `is_empty()` 追加
- [x] `pdf_loader_adapter.py`: `_split_text()` を `SpacyTextSplitter` に変更
- [x] `pdf_loader_adapter.py`: `tokenize()` に NUM, ストップワード, 単文字フィルタ, レンマ化を追加
- [x] `pdf_loader_adapter.py`: `load()` に NFKC 正規化を追加
- [x] `gradio_handler.py`: 空入力チェック + PDF 未ロードガードを追加

### notebook 08 更新

- [x] pip install セルに `langchain-text-splitters` を追加

### 永続的ドキュメント更新

- [x] `docs/architecture.md` に Embedding プレフィックス・SpacyTextSplitter・NFKC 正規化・トークナイザー詳細を記載

### 品質チェック

- [x] 既存テスト 39 件パス
- [x] Ruff チェッククリーン
