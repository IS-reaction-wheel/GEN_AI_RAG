## 機能設計書（FD）の作成指示

必ずディレクトリ内の `CLAUDE.md` と `README.md`、および `docs/product-requirements.md` (PRD) を参照し、機能設計書（`docs/functional-design.md`）を作成してください。
`CLAUDE.md` の規定に従い、アーキテクチャ、システム構成図、データモデル定義、コンポーネント設計などを網羅してください。

### 設計のコア要件（Clean Architectureの具現化）
PRDの「NFR-02」で定義されたアーキテクチャ方針と、`README.md` に記載された技術スタックを、具体的なPythonのモジュール構成とクラス設計に落とし込んでください。

#### 1. ディレクトリ構成（層の分離）
- `README.md` に記載されている既存のフォルダ構成（`src/`, `notebook/`, `app/`等）を前提とし、`src/` 配下を Clean Architecture の層に基づいて分割したツリー構造（`domain`, `usecases`, `interfaces`, `infrastructure` など）を提示してください。
- PRDで言及された「データ読み込み〜チャンク分割の前処理モジュール」がどこに配置され、どのように差し替え可能になるかを説明してください。

#### 2. コンポーネント設計と依存関係の逆転（DI）
- 主要なコンポーネント（LLMクライアント、ベクトルストア、データローダー、AIエージェントのワークフロー等）がどの層に属するかを整理してください。
- `README.md` に記載された具体的な技術（Ollama, Chroma DB, Sentence Transformers, LangGraph, Gradio）を各コンポーネントにマッピングしてください。
- `usecases` または `domain` 層で定義するインターフェース（抽象クラス / `typing.Protocol` など）と、それを実装する `infrastructure` 側のアダプタ（OllamaAdapter, ChromaDBAdapter等）のクラス図をMermaid記法で作成し、DI（依存性の注入）がどのように行われるかを可視化してください。

#### 3. Agentic RAG のシステム構成とフロー
- Jupyter Notebook（Mainルーチン）からUI（Gradio）を起動し、ユーザーの入力がどのように各層を伝播して Agentic RAG の自己修正ループ（LangGraph）を実行し、回答を返すかのフローを、シーケンス図（Mermaid記法）またはシステム構成図（Mermaid記法）で示してください。

上記の条件を踏まえ、`docs/functional-design.md` の内容を出力してください。