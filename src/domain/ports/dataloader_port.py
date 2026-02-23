"""データローダーのインターフェース"""

from typing import Protocol

from domain.models import DocumentChunk


class DataLoaderPort(Protocol):
    """ファイルからテキストを抽出しチャンク分割するインターフェース"""

    def load(self, file_path: str) -> list[DocumentChunk]:
        """ファイルからテキストを抽出しチャンク分割して返す"""
        ...
