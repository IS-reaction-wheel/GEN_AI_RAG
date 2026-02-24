# spaCy 辞書を ja_ginza に変更: 設計

## 実装アプローチ

### 変更点

`ja_core_news_sm` → `ja_ginza` への単純な置き換え。キャッシュ構造やフォールバック動作は変更しない。

### 変更箇所

| ファイル | 変更内容 |
|---|---|
| `src/interfaces/adapters/pdf_loader_adapter.py` | `_get_nlp()` 内の `spacy.load("ja_core_news_sm")` → `spacy.load("ja_ginza")` |
| `notebook/08_Agentic_RAG_Main.ipynb` セル2 | pip install に `ginza`, `ja-ginza` を追加 |
| `notebook/08_Agentic_RAG_Main.ipynb` セル3 | `spacy download ja_core_news_sm` → `spacy.load("ja_ginza")` の確認コードに変更 |
| `docs/architecture.md` | spaCy モデル名を `ja_ginza`（GiNZA）と明記 |

### GiNZA の特徴

- `pip install ginza ja-ginza` で辞書が同梱されるため `spacy download` が不要
- Universal Dependencies 準拠の高精度な形態素解析
- notebook 04〜07 で使用実績あり

## 影響範囲の分析

- **pdf_loader_adapter.py** — `_get_nlp()` の1行のみ変更。`tokenize()` のインターフェースは不変
- **テスト** — `tokenize()` のテストは spaCy モデルをモックしているため影響なし
- **永続的ドキュメント** — `architecture.md` に spaCy モデル名を明記する更新が必要
