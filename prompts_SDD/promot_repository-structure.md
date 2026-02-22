## リポジトリ構造定義書（repository-structure.md）の作成指示

必ずディレクトリ内の `CLAUDE.md`、`README.md`、および `docs/functional-design.md` (FD) を参照し、本プロジェクトのリポジトリ構造定義書（`docs/repository-structure.md`）を作成してください。

`CLAUDE.md` の規定に従い、以下の項目を網羅してドキュメントを構成してください。

### 1. フォルダ・ファイル構成（全体ツリー）
`README.md` に記載されている全体のフォルダ構成をベースに、プロジェクトルート直下のディレクトリツリー（ASCIIアートまたはMermaid記法）を作成し、それぞれの役割を簡潔に記述してください。
- 必須で含めるディレクトリ: `app/`, `data/`, `docs/`, `notebook/`, `outputs/`, `scripts/`, `src/`, `tests/`, `.steering/`
- ルート直下の主要ファイル: `README.md`, `CLAUDE.md`, `.env` (用途も併記)

### 2. `src/` 配下の詳細構造（Clean Architecture）
FDで定義されたアーキテクチャに従い、`src/` ディレクトリ内部の構造を詳細に定義してください。
各層（ディレクトリ）の役割と、そこに配置すべきコンポーネントのルールを記述してください。
- `domain/`: ドメインモデル（Pydantic等）とPort（Protocolによるインターフェース定義）
- `usecases/`: Agentic RAGのワークフロー（LangGraph）やエージェントノードのビジネスロジック
- `interfaces/`: Portを実装するインフラアダプタ（Ollama, ChromaDB等の呼び出し）やUIハンドラ（Gradio関連）
- `infrastructure/`: DIコンテナ（依存性の組み立て）

### 3. ドキュメントとタスク管理の構造（仕様駆動開発）
`CLAUDE.md` に定義されている、本プロジェクト特有のドキュメント管理手法について、ディレクトリ構造の観点から記述してください。
- `docs/`: アプリケーション全体の基本設計を定義する「永続的ドキュメント」の配置ルール
- `.steering/`: 作業単位の「一時的なステアリングファイル」の配置ルールと命名規則（`[YYYYMMDD]-[開発タイトル]/`）

### 4. ファイル配置と命名ルール
プロジェクト全体の秩序を保つためのルールを定義してください。
- **Pythonモジュール**: `src/` 配下のファイル命名規則（スネークケース等）と配置ルール（層をまたいだ直接参照の禁止など、DIの原則に基づくルール）。
- **Notebook**: `notebook/` 配下でのメインルーチン（.ipynb）の命名・配置ルール。
- **テストコード**: `tests/` 配下のディレクトリ構造（`src/` の構造をミラーリングするなど）とファイル命名規則（`test_*.py`）。

上記の条件を踏まえ、`docs/repository-structure.md` の内容をMarkdown形式で出力してください。