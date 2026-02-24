# 検索品質の修正: notebook 07 との機能差異解消

## 背景

notebook 07 を保守可能な Clean Architecture スクリプトに移行した際、検索品質に関わる処理ロジックの移植が不完全であった。notebook 07 との比較評価で5つの機能差異が特定された。

## 要求内容

### 1. Ruri-v3 Embedding プレフィックスの追加（重大）

- `DIContainer._create_embedding_fn()` で生成される embedding 関数に、ruri-v3 が要求するプレフィックスを追加する
  - ドキュメント登録時: `"検索文書: "` プレフィックス
  - クエリ検索時: `"検索クエリ: "` プレフィックス
- `ChromaDBAdapter` の `add_documents()` と `similarity_search()` でプレフィックスが適切に適用されること

### 2. SpacyTextSplitter によるチャンク分割（重大）

- `PDFLoaderAdapter._split_text()` の固定長文字スライスを、LangChain の `SpacyTextSplitter` による文境界考慮の分割に置き換える
- パラメータ: `separator="\n\n"`, `pipeline="ja_ginza"`, `chunk_size=500`, `chunk_overlap=100`

### 3. トークナイザーの完全移植（中程度）

- `tokenize()` に以下のフィルタを追加:
  - POS に `NUM` を追加
  - ストップワード除去 (`token.is_stop`)
  - 単文字ノイズ除去（ひらがな・記号の1文字トークン）
  - 見出し語化 (`token.lemma_`)

### 4. NFKC 正規化の追加（軽微）

- `PDFLoaderAdapter.load()` で `unicodedata.normalize("NFKC", ...)` を適用する

### 5. 入力バリデーションの追加（軽微）

- `GradioHandler.respond()` に空入力チェックを追加
- `GradioHandler.respond()` に PDF 未ロード時のガードを追加

## ユーザーストーリー

- 開発者として、src/ の検索品質が notebook 07 と同等であることを保証したい

## 受け入れ条件

- [ ] Embedding 関数がクエリ時に `"検索クエリ: "`, ドキュメント時に `"検索文書: "` プレフィックスを付与すること
- [ ] チャンク分割が `SpacyTextSplitter` により文境界を考慮すること
- [ ] `tokenize()` が notebook 07 と同等のフィルタリング（NUM, ストップワード, 単文字, レンマ化）を行うこと
- [ ] PDF テキストに NFKC 正規化が適用されること
- [ ] 空入力・PDF 未ロード時にエラーメッセージが表示されること
- [ ] 既存テスト 39 件がすべてパスすること
- [ ] Ruff チェックがクリーンであること

## 制約事項

- Ports（Protocol）のインターフェースは変更しない
- `split_into_safe_blocks()` のブロック分割ロジックは維持する（overlap_chars はデフォルト100のまま）
- notebook 08 のセルも必要に応じて更新する
