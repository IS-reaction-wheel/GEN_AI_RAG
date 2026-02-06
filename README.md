# GEN_AI_RAG
**生成AI＋RAG＋AIエージェントのテスト実装のリポジトリです。**


#### 目標
- OSSのモデル ＋（インメモリ）ベクトルデータベース ＋ 自己修正機能（AIエージェント）＋ GradioのUIまでの構築。
- 上記の各要素を実装するためのノートブック作成
- Github / Google Colab のテスト使用

#### 環境
- 開発環境：Windows / Python / VS Code / Claude Code
- 計算環境：Google Colab（VS Code 拡張機能経由で使用）
- AI開発フレームワーク：LangGraph / LangChain
- LLM/Embeddingモデル：OSSモデル。Hugging Faceに接続・量子化して構築
- LLMバックエンド：transformers + bitsandbytes（本番環境移行時は、Ollamaなど、サーバ管理されたものを使用する必要が生じる可能性あり。 `notebook/02_chat_langgraph_langchain.ipynb` 参照）
- ベクトルデータベース：Chroma DB（インメモリ使用）

#### フォルダ・ファイル構成
|フォルダ・ファイル|説明|備考|
|:---|:---|:---|
|app/|Gradio UIのスクリプト|-|
|data/|RAGで読み込みするテストデータ（PDF）|githubには未アップロード|
|notebook/|各実装要素の確認用|-|
|outputs/|ファイル出力|-|
|src/|主要な実装コード|-|
|scripts/|前処理や読み込みモデルなどのチューニングが必要なコード|-|
|tests/|単体テストコード|-|
|.env|環境変数設定|githubには未アップロード|
|CLAUDE.md|Claude Code 向けの開発ルールとコマンド参照|-|
|README.md|本リポジトリの概要|この画面のdoc|


#### 参考文献
1. [浅野純季，木村真也，田中冬馬，武藤克大，栁泉穂, 先輩データサイエンティストからの指南書 -実務で生き抜くためのエンジニアリングスキル, 技術評論社, 2025](https://gihyo.jp/book/2025/978-4-297-15100-3)
   > 環境構築全般（Pythonのパッケージマネージャ～プロジェクトのフォルダ構成など）
2. [藤原惟, Markdownライティング入門　プレーンテキストで気楽に書こう！, インプレス NextPublishing, 2018](https://nextpublishing.jp/book/10278.html)
   > markdownの基本的な使い方
3. [高野海斗, 齋藤慎一朗, 石原祥太郎, Kaggleではじめる大規模言語モデル入門, 講談社, 2026](https://www.kspub.co.jp/book/detail/5415245.html)
    > transformersでのLLMモデル呼び出しにおける量子化の解説
4. [山田育矢, 鈴木正敏，山田康輔，李凌寒, 大規模言語モデル入門, 技術評論社, 2023](https://gihyo.jp/book/2023/978-4-297-13633-8)
5. [山田育矢, 鈴木正敏，西川荘介，藤井一喜，山田康輔，李凌寒, 大規模言語モデル入門Ⅱ 〜生成型LLMの実装と評価, 技術評論社, 2024](https://gihyo.jp/book/2024/978-4-297-14393-0)
    > LLMの基礎原理やtransformersでの実装方法の解説（ただし、実装における計算条件の設定などは、各ページに分散されている。）

    > transformers-Hugging Face-LangChain間の接続は、大規模言語モデル入門Ⅱに記載がある。（ただし、本リポジトリでの実装のやり方は少し変えています。）
6. [John Berryman, Albert Ziegler 著, 服部佑樹, 佐藤直生 訳, LLMのプロンプトエンジニアリング ―GitHub Copilotを生んだ開発者が教える生成AIアプリケーション開発, オライリー・ジャパン, 2025](https://www.oreilly.co.jp/books/9784814401130/)
    > LLMの基礎原理の解説（3, 4より難しいが、LLMの仕組みの本質的なイメージが説明されている。）
7. [Mayo Oshin, Nuno Campos 著, 新井翔太, 嶋田健志 訳, 初めてのLangChain ―LangChainとLangGraphによるAI/LLMアプリケーションの構築, オライリー・ジャパン, 2025](https://www.oreilly.co.jp/books/9784814401307/)
    > 2026/02時点で、LangGraphによるメモリ管理の記述がある和書
8. [西見公宏，吉田真吾，大嶋勇樹, LangChainとLangGraphによるRAG・AIエージェント［実践］入門, 技術評論社, 2024](https://gihyo.jp/book/2024/978-4-297-14530-9)
    > LangChain/LangGraphについて、2026/02時点で最も詳細な解説。ただし出版日が古く、メモリ管理の記述が古い。
9. [李碩根, からあげ, 渡邊拓夢, PythonではじめるMCP開発入門, 講談社サイエンティフィク, 2025](https://www.kspub.co.jp/book/detail/5412381.html)
    > MCPサーバの仕組みから実装方法までの解説