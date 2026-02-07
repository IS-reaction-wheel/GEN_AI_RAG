# notebook_transformers

transformers + HuggingFacePipeline をLLMバックエンドとして使用したノートブック群。
現在は **Ollama ベースの実装（`notebook/`）に移行済み**。

## 収録ノートブック

| ファイル | 内容 |
|---|---|
| `01_connect_oss_llm_transformers.ipynb` | HuggingFace OSS LLM への接続 |
| `02_chat_langgraph_langchain_transformers.ipynb` | LangGraph + LangChain によるチャット実装 |
| `03_01_AI_Agent_ReAct_transformers.ipynb` | ReAct Web検索エージェント（MCP + DuckDuckGo） |

## バックエンド変更の経緯

### 問題: ChatHuggingFace のツールコール未対応

`ChatHuggingFace`（`HuggingFacePipeline` バックエンド）は、`bind_tools()` でツール定義を受け取るが
`apply_chat_template` に渡さない既知の不具合がある（[langchain #29033](https://github.com/langchain-ai/langchain/issues/29033)）。

ReAct エージェントを動作させるために、以下の3つのモンキーパッチが必要だった:

1. **`_to_chatml_format`**: ToolMessage / tool_calls 付き AIMessage への対応
2. **`_generate`**: ツール定義の注入 + `model.generate(skip_special_tokens=False)` による特殊トークン保持 + 複数形式のツールコールパーサー
3. **`_agenerate`**: 非同期コンテキスト対応（MCPツールが非同期専用のため）

### 問題: モデル選定の制約

- **granite-4.0-h-micro**: Mamba-Attention ハイブリッド構造のため、ツール定義を含む長いプロンプトで Mamba レイヤーが ~12GB の中間テンソルを生成。T4 GPU (15GB) では量子化しても VRAM 不足。
- **granite-3.3-2b-instruct**: 動作するが、2B モデルでは `do_sample=True` 時にツールコール生成が不安定。

### 結論

パッチの保守コストが高く、モデルごとの挙動差も大きいため、
ツールコールをネイティブサポートする **Ollama + ChatOllama** に移行した。
パッチなしで `bind_tools()` → ReAct ループが動作し、モデル切り替えも容易になる。
