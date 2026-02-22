# 開発ガイドライン（Development Guidelines）

## 1. コーディング規約とスタイル

### 1.1 基本スタイル

本プロジェクトは **PEP 8** に準拠した Python コードを記述する。コードフォーマッターおよびリンターには **Ruff** を使用し、コードの一貫性を維持する。

| 項目 | ルール |
|---|---|
| フォーマッター / リンター | Ruff（`ruff format` + `ruff check`） |
| 最大行長 | 88 文字（Ruff デフォルト） |
| インデント | スペース 4 つ |
| クォート | ダブルクォート `"` を標準とする |
| インポート順序 | 標準ライブラリ → サードパーティ → ローカルモジュールの順。Ruff の `isort` ルールで自動整列する |
| 末尾カンマ | 複数行の引数・要素には末尾カンマを付与する |

### 1.2 型ヒント（Type Hints）

すべての関数・メソッドに **型ヒントを完全付与する**ことを義務とする。`typing` モジュールを使用し、静的解析ツールによる型チェックを前提とした開発を行う。

```python
# 良い例
def search_documents(query: str, top_k: int = 10) -> list[SearchResult]:
    ...

# 悪い例（型ヒントがない）
def search_documents(query, top_k=10):
    ...
```

- 戻り値が `None` の場合も `-> None` を明記する
- `Optional[X]` よりも `X | None` 記法を推奨する（Python 3.10+）
- コレクション型は `list[str]`、`dict[str, int]` のように具体的な要素型を指定する
- `Any` の使用は極力避け、やむを得ない場合はコメントで理由を記載する

### 1.3 Docstring 規約

Docstring は **Google スタイル** を基本とする。ただし、型ヒントの完全付与を義務化しているため、`Args:` / `Returns:` セクションは型ヒントと重複するため**原則省略**し、概要の記述に重点を置く。

#### 記述ルール

| 対象 | 必須 / 任意 | 記述内容 |
|---|---|---|
| クラス | 必須 | 1行の概要（クラスの責務を簡潔に説明） |
| Port（Protocol）のメソッド | 必須 | 何をするかの概要 |
| 公開関数（`_` プレフィックスなし） | 必須 | 概要のみ。引数・戻り値の説明は型ヒントに委ねる |
| プライベート関数・自明なメソッド | 任意 | ロジックが複雑な場合のみ記述 |

#### 例

```python
class JudgeResult(BaseModel):
    """十分性判定ノードの出力"""

    sufficient: bool = Field(description="情報が十分かどうか")
    reason: str = Field(description="判断理由")
    additional_subtasks: list[Subtask] | None = Field(default=None)

    @model_validator(mode="after")
    def force_consistency(self):
        """LLM 出力の論理矛盾を自動補正する。"""
        ...


class VectorStorePort(Protocol):
    """ベクトルストアのインターフェース"""

    def add_documents(self, chunks: list[DocumentChunk]) -> None:
        """ドキュメントチャンクをベクトル DB に追加する"""
        ...

    def similarity_search(self, query: str, k: int = 10) -> list[SearchResult]:
        """ベクトル類似度検索を実行する"""
        ...


def clean_pdf_text(text: str) -> str:
    """PDF から抽出したテキストのノイズを除去する。"""
    ...
```

#### 補足

- `Args:` / `Returns:` セクションは、型ヒントだけでは意味が伝わらない場合（例: 単位や制約条件がある場合）にのみ追加する
- Pydantic モデルのフィールド説明は `Field(description=...)` に記載する（LLM の構造化出力精度にも寄与するため）

### 1.4 データモデルの定義

データの保持や LLM の構造化出力には、`dataclass` ではなく **Pydantic `BaseModel`** を使用する（FD セクション 5.1）。

| 用途 | 採用するクラス | 理由 |
|---|---|---|
| LLM 構造化出力（`with_structured_output` 用） | Pydantic `BaseModel` | LangChain との直接連携、バリデーション |
| ドメインモデル（データ保持） | Pydantic `BaseModel` | バリデーション、シリアライズの統一性 |
| LangGraph ワークフロー状態 | `TypedDict` | LangGraph の State 定義の標準パターン |

```python
# 良い例（Pydantic BaseModel）
from pydantic import BaseModel, Field

class Subtask(BaseModel):
    purpose: str = Field(description="このサブタスクで明らかにしたいこと")
    queries: list[str] = Field(description="検索クエリのリスト")

# 悪い例（dataclass）
from dataclasses import dataclass

@dataclass
class Subtask:
    purpose: str
    queries: list[str]
```

### 1.5 エラーハンドリング

LLM の出力異常やタイムアウトに対しては、FD セクション 11.5 で定義された **多層防御戦略** に基づくエラーハンドリングを実装する。

#### エラーハンドリングの原則

1. **ワークフローを異常終了させない**: 例外発生時はフォールバック値で処理を継続する
2. **具体的な例外をキャッチする**: `except Exception` ではなく、想定される例外を明示的にキャッチする。ただし、LLM 出力のパース失敗など予測困難な例外に対しては `except Exception` による包括的なキャッチを許容する
3. **フォールバック値を事前に設計する**: 各ノードのフォールバック値を明確に定義する

#### 構造化出力ノードのエラーハンドリングパターン

```python
try:
    result = await asyncio.wait_for(
        structured_llm.ainvoke(messages),
        timeout=config.structured_output_timeout,
    )
except asyncio.TimeoutError:
    # タイムアウト → フォールバック
    result = fallback_value
except Exception:
    # Pydantic バリデーション失敗等 → フォールバック
    result = fallback_value
```

#### 防御層の一覧

| 防御層 | 機構 | 対処 |
|---|---|---|
| 型バリデーション | Pydantic `BaseModel` | 不正な JSON → `ValidationError` をキャッチしフォールバック値で継続 |
| 論理整合性補正 | `@model_validator(mode="after")` | LLM 出力の論理矛盾を自動補正 |
| タイムアウト | `asyncio.wait_for()` | ノードごとに個別タイムアウトを設定 |
| 出力トークン制限 | `num_predict` パラメータ | LLM の長考（推論疲れ）を防止 |
| ループ上限 | `max_loop_count` | judge → doc_search の無限ループを防止 |

---

## 2. 命名規則

### 2.1 一般的な命名

| 対象 | 命名規則 | 例 |
|---|---|---|
| クラス名 | パスカルケース（`PascalCase`） | `AgentWorkflow`, `SearchResult` |
| メソッド・関数名 | スネークケース（`snake_case`） | `search_documents`, `build_graph` |
| 変数名 | スネークケース（`snake_case`） | `search_results`, `loop_count` |
| 定数 | アッパースネークケース（`UPPER_SNAKE_CASE`） | `MAX_LOOP_COUNT`, `DEFAULT_TOP_K` |
| モジュール名（ファイル名） | スネークケース（`snake_case`） | `agent_workflow.py`, `ollama_adapter.py` |
| パッケージ名（ディレクトリ名） | スネークケース（`snake_case`） | `domain`, `usecases`, `interfaces` |

### 2.2 アーキテクチャ固有の命名サフィックス

Clean Architecture と LangGraph を採用した本プロジェクト固有の命名規則を以下に定める。

| 層 | 対象 | サフィックス | 例 |
|---|---|---|---|
| Domain | インターフェース（Protocol） | `[名前]Port` | `LLMPort`, `VectorStorePort`, `RerankerPort`, `DataLoaderPort` |
| Interface Adapters | Port の具象実装クラス | `[名前]Adapter` | `OllamaAdapter`, `ChromaDBAdapter`, `RerankerAdapter`, `PDFLoaderAdapter` |
| Use Cases | エージェントノード関数 | `[処理内容]_node` | `task_planning_node`, `doc_search_node`, `summarize_node`, `judge_node`, `generate_answer_node` |
| Use Cases | ワークフロー状態 | `[名前]State` | `WorkflowState` |
| Use Cases | LLM 構造化出力モデル | `[名前]Result` | `TaskPlanningResult`, `JudgeResult` |
| Infrastructure | DI コンテナ | `DIContainer` | `DIContainer` |
| Interface Adapters | UI ハンドラ | `[名前]Handler` | `GradioHandler` |

### 2.3 ハイパーパラメータ設定

ハイパーパラメータの設定クラスは `WorkflowConfig`（Pydantic `BaseSettings`）に集約する。環境変数から上書きする場合は `RAG_` プレフィックスを使用する。

```python
# 環境変数での上書き例
RAG_LLM_TEMPERATURE=0.5
RAG_RETRIEVAL_TOP_K=30
```

---

## 3. テスト規約

### 3.1 テストフレームワーク

テストフレームワークには **pytest** を使用する。

### 3.2 テストディレクトリ構成

```
tests/
├── unit/                          # ユニットテスト
│   ├── test_models.py             # Pydantic モデルのバリデーションテスト
│   ├── test_data_preprocessing.py # データ前処理（純粋関数）のテスト
│   ├── test_task_planning_node.py # タスク分割ノードのテスト
│   ├── test_doc_search_node.py    # ドキュメント検索ノードのテスト
│   ├── test_summarize_node.py     # 要約ノードのテスト
│   ├── test_judge_node.py         # 判定ノードのテスト
│   └── test_data_ingestion.py     # データ取り込みユースケースのテスト
├── integration/                   # 統合テスト
│   ├── test_ingestion_pipeline.py # データ取り込みパイプライン全体
│   └── test_agent_workflow.py     # AgentWorkflow 全体フロー
└── conftest.py                    # 共通フィクスチャ
```

### 3.3 ユニットテストの原則

#### DI（依存性の注入）を活用したモックの注入

外部依存（LLM、Chroma DB、Sentence Transformers、spaCy モデル等）を切り離すため、テスト時には Port のモック（Mock / Stub）を注入する。

```python
# テストでのモック注入例
class MockVectorStore:
    """VectorStorePort のモック実装"""
    def similarity_search(self, query: str, k: int = 10) -> list[SearchResult]:
        return [SearchResult(chunk=mock_chunk, score=0.9)]

    def keyword_search(self, query: str, k: int = 10) -> list[SearchResult]:
        return [SearchResult(chunk=mock_chunk, score=0.8)]

class MockReranker:
    """RerankerPort のモック実装"""
    def rerank(self, query: str, results: list[SearchResult], top_k: int = 5) -> list[SearchResult]:
        return results[:top_k]

def test_doc_search_node():
    node = DocSearchNode(vectorstore=MockVectorStore(), reranker=MockReranker())
    state = WorkflowState(...)
    result = node(state)
    assert len(result["search_results"]) > 0
```

#### 純粋関数のテスト

前処理や文字列操作など、外部依存のない純粋関数（PDF テキストのクリーニング、ブロック分割、形態素解析等）に対するテストを徹底する。これらは LLM や DB のモックなしで高速にテストできる。

```python
# 純粋関数のテスト例
class TestCleanPdfText:
    def test_removes_single_char_line_blocks(self):
        """1文字行が3行以上連続するブロックが除去されることを検証する。"""
        text = "正常なテキスト\nあ\nい\nう\n正常なテキスト"
        result = clean_pdf_text(text)
        assert "あ\nい\nう" not in result

    def test_preserves_normal_text(self):
        """正常なテキストが変更されないことを検証する。"""
        text = "これは正常なテキストです。\n\n次の段落です。"
        result = clean_pdf_text(text)
        assert result == text
```

#### バリデーションテスト

Pydantic モデルの `@model_validator` による論理整合性補正ロジックのテストを必ず作成する。

```python
# バリデーションテスト例
def test_judge_result_force_consistency_no_additional_subtasks():
    """sufficient=False かつ additional_subtasks が空の場合、
    sufficient=True に自動補正されることを検証する。"""
    result = JudgeResult(
        sufficient=False,
        reason="情報が不足しています",
        additional_subtasks=None,
    )
    assert result.sufficient is True
    assert "現状の情報で回答します" in result.reason
```

### 3.4 テスト命名規則

| 要素 | 規則 | 例 |
|---|---|---|
| テストファイル名 | `test_[対象モジュール名].py` | `test_models.py`, `test_doc_search_node.py` |
| テストクラス名 | `Test[対象クラス/関数名]` | `TestCleanPdfText`, `TestJudgeResult` |
| テストメソッド名 | `test_[テスト対象の振る舞い]` | `test_removes_single_char_line_blocks` |
| テストの docstring | 日本語で「何を検証するか」を記述 | `"""1文字行ブロックが除去されることを検証する。"""` |

### 3.5 テスト対象の優先度

| 優先度 | 対象 | 理由 |
|---|---|---|
| **高** | Pydantic モデルの `@model_validator` | LLM 出力の論理矛盾を自動補正する重要なロジック |
| **高** | データ前処理（クリーニング・分割・トークナイズ） | RAG の検索精度に直結する純粋関数 |
| **中** | 各エージェントノード（モック注入） | ワークフローの各ステップの入出力検証 |
| **中** | DataIngestion（モック注入） | データ取り込みパイプラインの検証 |
| **低** | 統合テスト（ワークフロー全体） | モックを注入した E2E フロー検証 |

---

## 4. バージョン管理（Git）とドキュメント更新規約

### 4.1 コミットメッセージ

**Conventional Commits** に基づくプレフィックスを使用した明確なコミットメッセージを記述する。

| プレフィックス | 用途 | 例 |
|---|---|---|
| `feat:` | 新機能の追加 | `feat: タスク分割ノードを実装` |
| `fix:` | バグ修正 | `fix: JudgeResult の論理補正ロジックを修正` |
| `docs:` | ドキュメントの変更 | `docs: 機能設計書のデータモデル定義を更新` |
| `test:` | テストの追加・修正 | `test: clean_pdf_text のユニットテストを追加` |
| `refactor:` | リファクタリング（機能変更なし） | `refactor: DI コンテナの初期化処理を整理` |
| `style:` | コードスタイルの変更（動作に影響なし） | `style: Ruff のフォーマットを適用` |
| `chore:` | ビルド・ツール設定の変更 | `chore: pyproject.toml に Ruff 設定を追加` |

#### コミットメッセージのフォーマット

```
<プレフィックス>: <変更内容の要約>

<変更の詳細（必要な場合）>
```

### 4.2 ドキュメントとコードの同期

本プロジェクトは **仕様駆動開発（SDD）** を採用しており、設計ドキュメントとコードの同期を維持することが最重要のルールである。

#### 同期ルール

1. **コードの変更（特にアーキテクチャやデータモデルの変更）が発生した場合**:
   - `.steering/` でタスク管理を行う
   - 必要に応じて `docs/` の設計ドキュメント（FD 等のダイアグラム含む）を**必ずコードと一緒に更新**する

2. **設計ドキュメントの更新が必要なケース**:
   - Port（インターフェース）の追加・変更
   - ドメインモデル（Pydantic `BaseModel`）のフィールド追加・変更
   - ワークフロー状態（`WorkflowState`）の変更
   - エージェントノードの追加・削除
   - 新しいアダプタの追加
   - ハイパーパラメータ（`WorkflowConfig`）の追加・変更

3. **図表・ダイアグラムの更新**:
   - Mermaid 記法で記載された図表は、対応するコード変更と同時に更新する
   - CLAUDE.md の「図表・ダイアグラムの記載ルール」に従い、関連するドキュメント内に直接記載する

---

## 5. AI コーディング（Claude Code）運用ガイドライン

### 5.1 ステップバイステップの実装

`.steering/` 配下の `tasklist.md` に基づき、以下のルールで実装を進める。

1. **一度に大量のファイルを変更・生成しない**: 1つのコンポーネント（または1つのテスト）ごとに着実に実装する
2. **テストファーストを推奨**: 可能な場合、テストを先に書いてから実装コードを作成する
3. **コミット粒度**: コンポーネント単位またはテスト単位で細かくコミットする
4. **動作確認**: 各ステップの実装後にリント・型チェックを実施する

#### 実装の進め方（例）

```
1. Domain 層のモデル定義（models.py）を実装
   → テスト（test_models.py）を作成・実行
   → コミット

2. Domain 層の Port 定義（ports/）を実装
   → コミット

3. Use Cases 層のノード関数を1つずつ実装
   → 各ノードのテスト（モック注入）を作成・実行
   → コミット

4. Interface Adapters 層のアダプタを1つずつ実装
   → コミット

5. Infrastructure 層の DI コンテナを実装
   → 統合テストを作成・実行
   → コミット
```

### 5.2 勝手な仕様変更・ライブラリ追加の禁止

実装中に行き詰まった場合でも、以下の行為を禁止する。

1. **設計書で定められたアーキテクチャ（層の分離など）を勝手に崩さない**
   - Clean Architecture の依存性のルールを遵守する
   - 上位層（Domain / Use Cases）から下位層（Infrastructure）への直接依存を作らない

2. **新たな外部パッケージが必要になった場合は、事前に提案し承認を得る**
   - `pyproject.toml` への依存追加は承認後に行う
   - 既存のライブラリで代替可能かを先に検討する

3. **FD（機能設計書）で定義されたデータモデルやインターフェースを勝手に変更しない**
   - 変更が必要な場合は、まず設計ドキュメントの更新を提案する

### 5.3 コード品質チェックリスト

実装の各ステップにおいて、以下を確認する。

- [ ] 型ヒントがすべての関数・メソッドに付与されているか
- [ ] Ruff によるフォーマット・リントエラーがないか
- [ ] アーキテクチャ固有の命名サフィックスが正しく適用されているか
- [ ] 上位層から下位層への直接依存がないか（依存性のルール）
- [ ] Pydantic `BaseModel` を使用しているか（`dataclass` を使っていないか）
- [ ] エラーハンドリングでフォールバック値が定義されているか
- [ ] 設計ドキュメントとコードの整合性が取れているか
