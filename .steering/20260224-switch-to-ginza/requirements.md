# spaCy 辞書を ja_ginza に変更

## 背景

初回実装では spaCy の日本語モデルとして `ja_core_news_sm` を使用していたが、notebook 04〜07 では一貫して `ja_ginza`（GiNZA）を使用している。notebook と `src/` の間で辞書を統一する。

## 要求内容

- BM25 用トークナイズに使用する spaCy モデルを `ja_core_news_sm` から `ja_ginza` に変更する
- notebook 08 の pip install セルに `ginza` / `ja-ginza` パッケージを追加する
- notebook 08 の spaCy モデルダウンロードセルを GiNZA 用に変更する（`pip install` で辞書同梱のため `spacy download` 不要）

## ユーザーストーリー

- 開発者として、notebook と `src/` で同一の spaCy 辞書を使用し、形態素解析の結果を一貫させたい

## 受け入れ条件

- [x] `pdf_loader_adapter.py` の `_get_nlp()` が `ja_ginza` をロードすること
- [x] notebook 08 の pip install セルに `ginza`, `ja-ginza` が含まれること
- [x] notebook 08 の spaCy セルが `ja_ginza` の読み込み確認になっていること
- [x] 既存テスト 39 件がすべてパスすること
- [x] Ruff チェックがクリーンであること

## 制約事項

- `_get_nlp()` のキャッシュ構造・フォールバック動作は変更しない
- `docs/architecture.md` に spaCy モデル名を明記する（永続的ドキュメント更新）
