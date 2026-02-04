# GEN_AI_RAG
**生成AI＋RAG＋AIエージェントのテスト実装のリポジトリです。**

#### 目標
- OSSのモデル ＋（インメモリ）ベクトルデータベース ＋ 自己修正機能（AIエージェント）＋ GradioのUIまでの構築。
- 上記の各要素を実装するためのノートブック作成
- Github / Google Colab のテスト使用

#### 環境
- 開発環境：Windows / Python
- 計算環境：Google Colab
- AI開発フレームワーク：LangGraph / LangChain
- LLM/Embeddingモデル：OSSモデル。Hugging Faceに接続・量子化して構築
- ベクトルデータベース：Chroma DB（インメモリ使用）

#### フォルダ・ファイル構成
|フォルダ・ファイル|説明|
|:---|:---|
|app/|Gradio UIのスクリプト|
|data/|RAGで読み込みするテストデータ（PDF）|
|notebook/|各実装要素の確認用|
|outputs/|ファイル出力|
|src/|主要な実装コード|
|scripts/|前処理や読み込みモデルなどのチューニングが必要なコード|
|tests/|単体テストコード|