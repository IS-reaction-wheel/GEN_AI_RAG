# 検索品質の修正: 設計

## 実装アプローチ

notebook 07 の処理ロジックを忠実に移植する。Ports（Protocol）のインターフェースは変更しない。

## 変更箇所

### 1. Ruri-v3 Embedding プレフィックス

**ファイル**: `src/infrastructure/di_container.py`

`_create_embedding_fn()` が返す関数を2つに分離する。

```python
def _create_embedding_fn(self) -> tuple[callable, callable]:
    """document 用と query 用の embedding 関数を生成する。"""
    model = SentenceTransformer(self.config.embedding_model_name)

    def embed_documents(texts: list[str]) -> list[list[float]]:
        prefixed = [f"検索文書: {t}" for t in texts]
        return model.encode(prefixed, convert_to_numpy=True).tolist()

    def embed_query(texts: list[str]) -> list[list[float]]:
        prefixed = [f"検索クエリ: {t}" for t in texts]
        return model.encode(prefixed, convert_to_numpy=True).tolist()

    return embed_documents, embed_query
```

**ファイル**: `src/interfaces/adapters/chromadb_adapter.py`

コンストラクタで document 用と query 用の2つの embedding 関数を受け取る。

```python
def __init__(
    self,
    embedding_fn: Callable,      # ドキュメント登録用
    query_embedding_fn: Callable, # クエリ検索用
    ...
)
```

- `add_documents()`: `self._embedding_fn(texts)` — document プレフィックス付き
- `similarity_search()`: `self._query_embedding_fn([query])` — query プレフィックス付き

**ファイル**: `src/domain/ports/vectorstore_port.py`

Protocol のインターフェースは変更しない（embedding は内部実装の詳細）。

### 2. SpacyTextSplitter によるチャンク分割

**ファイル**: `src/interfaces/adapters/pdf_loader_adapter.py`

`_split_text()` メソッドを `SpacyTextSplitter` ベースに書き換える。

**重要**: `SpacyTextSplitter` のコンストラクタは内部で `spacy.load()` を呼ぶため、
ブロックごとに毎回生成するとパフォーマンスが大幅に劣化する。
notebook 07 と同様に `load()` 内で1度だけ生成し、全ブロックで再利用する。

```python
def load(self, file_path: str) -> list[DocumentChunk]:
    ...
    # SpacyTextSplitter は1度だけ生成して再利用
    splitter = SpacyTextSplitter(
        separator="\n\n",
        pipeline="ja_ginza",
        chunk_size=self._chunk_size,
        chunk_overlap=self._chunk_overlap,
    )
    for block in blocks:
        chunks = self._split_text(block, source, splitter)
        ...

def _split_text(self, text, source, splitter) -> list[DocumentChunk]:
    split_texts = splitter.split_text(text)
    return [
        DocumentChunk(chunk_id=str(uuid.uuid4()), text=t.strip(), source=source)
        for t in split_texts if t.strip()
    ]
```

### 3. トークナイザーの完全移植

**ファイル**: `src/interfaces/adapters/pdf_loader_adapter.py`

`tokenize()` を notebook 07 と同等に修正。

```python
def tokenize(text: str) -> list[str]:
    nlp = _get_nlp()
    if nlp is None:
        return text.split()

    doc = nlp(text)
    target_pos = {"NOUN", "VERB", "ADJ", "PROPN", "NUM"}
    tokens = []
    for token in doc:
        if token.pos_ not in target_pos:
            continue
        if token.is_stop:
            continue
        lemma = token.lemma_
        if len(lemma) == 1 and re.match(r"[ぁ-ん\u30fc!-/:-@\[-`{-~]", lemma):
            continue
        tokens.append(lemma)
    return tokens
```

### 4. NFKC 正規化

**ファイル**: `src/interfaces/adapters/pdf_loader_adapter.py`

`PDFLoaderAdapter.load()` で `clean_pdf_text()` の前に NFKC 正規化を挿入。

```python
import unicodedata

raw_text = result.text_content
cleaned = unicodedata.normalize("NFKC", raw_text)
cleaned = clean_pdf_text(cleaned)
```

### 5. 入力バリデーション

**ファイル**: `src/interfaces/ui/gradio_handler.py`

`respond()` の先頭にガードを追加。

```python
# 空入力の防止
if not message.strip():
    yield history, thinking_log, session_state
    return

# PDF 未ロード時のガード（VectorStorePort に has_documents() は不要。
# _doc_search 実行時に空の検索結果が返るため、ユーザーへのメッセージで対応）
```

PDF 未ロードチェックについて: notebook 07 ではグローバル変数 `_chunks` を直接参照できたが、src/ では `VectorStorePort` を通じた間接的なアクセスとなる。Protocol に `has_documents()` を追加するのは過剰なため、`ChromaDBAdapter` に `is_empty()` メソッドを追加し、`GradioHandler` のコンストラクタで `vectorstore` を保持する方式とする。

```python
# ChromaDBAdapter に追加
def is_empty(self) -> bool:
    return self._collection.count() == 0 and not self._chunks_cache

# GradioHandler.respond() でチェック
if self._vectorstore.is_empty():
    history = list(history) + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": "⚠️ PDFファイルを先にアップロードしてください。"},
    ]
    yield history, thinking_log, session_state
    return
```

## 影響範囲の分析

| ファイル | 変更内容 | テストへの影響 |
|---------|----------|--------------|
| `di_container.py` | embedding 関数を2つ生成、`ChromaDBAdapter` に2つ渡す | DI 結合テストに影響（モック調整） |
| `chromadb_adapter.py` | コンストラクタ引数追加 + `is_empty()` + query 用 embedding 分離 | アダプタテストのモック調整 |
| `pdf_loader_adapter.py` | `tokenize()` 強化 + `_split_text()` 書換 + NFKC 追加 | トークナイザーテストの期待値変更 |
| `gradio_handler.py` | 入力バリデーション追加 + `vectorstore` 保持 | UI テストに軽微な影響 |

## notebook 08 への影響

- `langchain-text-splitters` が pip install セルに含まれていることを確認する（`SpacyTextSplitter` の依存）
