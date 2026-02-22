# CLAUDE.md

Claude Code 向けの開発ルールとコマンド参照です。

## 環境・パッケージマネージャー

- Python **3.12**（`.python-version` で固定）
- パッケージマネージャー：**uv**

```bash
uv sync             # 全依存関係インストール（dev 含む）
uv add <pkg>        # ランタイム依存関係を追加
uv add --dev <pkg>  # dev 依存関係を追加
uv run <cmd>        # プロジェクト環境内で実行
```

## ディレクトリ構成

| パス | 役割 |
|---|---|
| `notebook/` | 実装検証用の Jupyter ノートブック |
| `src/` | メインの実装コード |
| `app/` | Gradio アプリスクリプト |
| `scripts/` | 前処理やチューニングスクリプト |
| `tests/` | ユニットテスト |
| `data/` | テストデータ — gitignore 済み |
| `outputs/` | 出力ファイル |

## 注意事項

- `.env`・`data/` は gitignore 済み。コミットしない。
- 計算リソース（GPU）は Google Colab を使用する前提。本PCにGPUはない。Colab へのアクセスは VS Code の Colab カーネル拡張経由。

## テスト実行

```bash
uv run pytest tests/
```
