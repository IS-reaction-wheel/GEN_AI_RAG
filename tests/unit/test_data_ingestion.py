"""データ取り込みユースケースのユニットテスト"""

from domain.models import DocumentChunk
from usecases.data_ingestion import DataIngestion


class _MockDataLoader:
    """DataLoaderPort のモック"""

    def __init__(self, chunks: list[DocumentChunk] | None = None) -> None:
        self._chunks = (
            chunks
            if chunks is not None
            else [
                DocumentChunk(
                    chunk_id="c1",
                    text="チャンク1",
                    source="test.pdf",
                    page=1,
                ),
                DocumentChunk(
                    chunk_id="c2",
                    text="チャンク2",
                    source="test.pdf",
                    page=2,
                ),
            ]
        )

    def load(self, file_path: str) -> list[DocumentChunk]:
        return self._chunks


class _MockVectorStore:
    """VectorStorePort のモック"""

    def __init__(self) -> None:
        self.stored_chunks: list[DocumentChunk] = []

    def add_documents(self, chunks: list[DocumentChunk]) -> None:
        self.stored_chunks.extend(chunks)

    def similarity_search(self, query: str, k: int = 10) -> list:
        return []

    def keyword_search(self, query: str, k: int = 10) -> list:
        return []


class TestDataIngestion:
    """DataIngestion のテスト"""

    def test_ingest_returns_chunk_count(self) -> None:
        """登録チャンク数が返されることを検証する。"""
        loader = _MockDataLoader()
        vectorstore = _MockVectorStore()
        ingestion = DataIngestion(loader=loader, vectorstore=vectorstore)

        count = ingestion.ingest("test.pdf")

        assert count == 2
        assert len(vectorstore.stored_chunks) == 2

    def test_ingest_empty_chunks(self) -> None:
        """チャンクが0件の場合、0が返されることを検証する。"""
        loader = _MockDataLoader(chunks=[])
        vectorstore = _MockVectorStore()
        ingestion = DataIngestion(loader=loader, vectorstore=vectorstore)

        count = ingestion.ingest("empty.pdf")

        assert count == 0
        assert len(vectorstore.stored_chunks) == 0
