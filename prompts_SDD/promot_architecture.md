## 技術仕様書（architecture.md）の作成指示

必ずディレクトリ内の `CLAUDE.md`、`README.md`、`docs/product-requirements.md` (PRD)、および `docs/functional-design.md` (FD) を参照し、本プロジェクトの技術仕様書（`docs/architecture.md`）を作成してください。

`CLAUDE.md` の規定に従い、以下の4つの項目を必ず網羅してドキュメントを構成してください。

### 1. テクノロジースタック
README.md および FD に記載されている具体的な技術要素を整理し、それぞれの採用理由と役割を記述してください。
- **フロントエンド / UI**: Gradio
- **バックエンド / ワークフロー**: Python, LangChain, LangGraph
- **LLM / 推論エンジン**: Ollama (モデル: gpt-oss:20b)
- **ベクトルデータベース**: Chroma DB (インメモリ使用)
- **Embedding / Reranker**: Sentence Transformers (モデル: cl-nagoya/ruri-v3-310m, cl-nagoya/ruri-v3-reranker-310m)
- **データ前処理 / 解析**: markitdown（PDF等の技術資料をLLMと相性の良いMarkdown形式に変換・構造化して抽出するため）、spaCy（日本語前処理用）など

### 2. 開発ツールと手法
本プロジェクトの開発環境と実行環境の特殊性、および設計手法について記述してください。
- **開発環境と実行環境の分離**: Windows / VS Code / Claude Codeでの開発と、Google Colab（Jupyter Notebook経由）でのテスト・実行というハイブリッド構成について明記してください。
- **アーキテクチャ手法**: FDで定義された「Clean Architecture（依存性のルール）」と「DI（依存性の注入）」を技術的にどのように実現しているか（Pydanticによる設定管理や、プロトコルを用いたインターフェース定義など）を説明してください。

### 3. 技術的制約と要件
完全オフライン動作を目指す製造業向けのAgentic RAGシステム特有の制約を定義してください。
- **インフラ制約**: 機密情報保護のための完全オフライン（オンプレミス想定）動作の必須要件。外部API（OpenAI等）を一切使用しない制約。
- **実行環境の制約**: プロトタイプ段階におけるGoogle Colabの計算資源（GPUメモリ制限など）の制約と、Jupyter NotebookがMainルーチンとなることへの対応。
- **データ制約**: 対象データが「未加工の技術資料」であることに対し、`markitdown` を用いてMarkdown化することで文書構造を保持したままチャンク分割し、検索精度を向上させるアプローチを記載してください。

### 4. パフォーマンス要件
Agentic RAGの自己修正ループやローカルLLMの特性を考慮したパフォーマンスに関する要件を定義してください。
- **レイテンシとUX**: 自律的な複数回推論（Thinking）により回答までに時間がかかることを前提とし、Gradio UIでのストリーミング出力や思考過程（Thinkingログ）のリアルタイム表示によってUXを担保する要件。
- **トークンとメモリ管理**: インメモリベクトルDB（Chroma DB）の容量制限、およびマルチターンチャット時におけるLLMのコンテキストウィンドウ枯渇や「推論疲れ」を防ぐための要約ノード（summarize）の役割について記述してください。

上記の条件を踏まえ、`docs/architecture.md` の内容をMarkdown形式で出力してください。