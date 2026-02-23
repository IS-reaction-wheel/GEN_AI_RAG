"""データ取り込みユースケース"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.ports.dataloader_port import DataLoaderPort
    from domain.ports.vectorstore_port import VectorStorePort

logger = logging.getLogger(__name__)


class DataIngestion:
    """PDF → チャンク分割 → ベクトル DB 格納のユースケース"""

    def __init__(
        self,
        loader: DataLoaderPort,
        vectorstore: VectorStorePort,
    ) -> None:
        self._loader = loader
        self._vectorstore = vectorstore

    def ingest(self, file_path: str) -> int:
        """ファイルからチャンクを生成しベクトル DB に格納する。

        Returns:
            登録されたチャンク数
        """
        logger.info("データ取り込みを開始: %s", file_path)

        chunks = self._loader.load(file_path)
        if not chunks:
            logger.warning("チャンクが0件のため、登録をスキップします。")
            return 0

        self._vectorstore.add_documents(chunks)
        logger.info("データ取り込み完了: %d チャンク", len(chunks))
        return len(chunks)
