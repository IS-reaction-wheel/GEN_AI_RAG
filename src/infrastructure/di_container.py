"""DI コンテナ（依存性の組み立て・注入）"""

from __future__ import annotations

import logging

from domain.config import WorkflowConfig
from interfaces.adapters.chromadb_adapter import ChromaDBAdapter
from interfaces.adapters.ollama_adapter import OllamaAdapter
from interfaces.adapters.pdf_loader_adapter import PDFLoaderAdapter, tokenize
from interfaces.adapters.reranker_adapter import RerankerAdapter
from interfaces.ui.gradio_handler import GradioHandler
from usecases.agent_workflow import AgentWorkflow
from usecases.data_ingestion import DataIngestion

logger = logging.getLogger(__name__)


class DIContainer:
    """すべての依存性を組み立て、コンストラクタインジェクションで注入する"""

    def __init__(self, config: WorkflowConfig | None = None) -> None:
        self.config = config or WorkflowConfig()
        self._llm: OllamaAdapter | None = None
        self._vectorstore: ChromaDBAdapter | None = None
        self._reranker: RerankerAdapter | None = None
        self._dataloader: PDFLoaderAdapter | None = None
        self._workflow: AgentWorkflow | None = None
        self._ingestion: DataIngestion | None = None

    def _create_embedding_fns(self) -> tuple[callable, callable]:
        """Sentence Transformers による Embedding 関数を生成する。

        ruri-v3 はドキュメント/クエリで異なるプレフィックスを要求するため、
        2つの関数を返す。
        """
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(self.config.embedding_model_name)
        logger.info("Embedding モデルをロード: %s", self.config.embedding_model_name)

        def embed_documents(texts: list[str]) -> list[list[float]]:
            prefixed = [f"検索文書: {t}" for t in texts]
            return model.encode(prefixed, convert_to_numpy=True).tolist()

        def embed_query(texts: list[str]) -> list[list[float]]:
            prefixed = [f"検索クエリ: {t}" for t in texts]
            return model.encode(prefixed, convert_to_numpy=True).tolist()

        return embed_documents, embed_query

    def create_llm(self) -> OllamaAdapter:
        """LLMPort の具体実装を生成する。"""
        if self._llm is None:
            self._llm = OllamaAdapter(
                model_name=self.config.llm_model_name,
                num_ctx=self.config.llm_num_ctx,
                temperature=self.config.llm_temperature,
                top_k=self.config.llm_top_k,
                top_p=self.config.llm_top_p,
                repeat_penalty=self.config.llm_repeat_penalty,
            )
            logger.info("OllamaAdapter を生成: model=%s", self.config.llm_model_name)
        return self._llm

    def create_vectorstore(self) -> ChromaDBAdapter:
        """VectorStorePort の具体実装を生成する。"""
        if self._vectorstore is None:
            embed_documents, embed_query = self._create_embedding_fns()
            self._vectorstore = ChromaDBAdapter(
                embedding_fn=embed_documents,
                query_embedding_fn=embed_query,
                tokenize_fn=tokenize,
            )
            logger.info("ChromaDBAdapter を生成")
        return self._vectorstore

    def create_reranker(self) -> RerankerAdapter:
        """RerankerPort の具体実装を生成する。"""
        if self._reranker is None:
            self._reranker = RerankerAdapter(
                model_name=self.config.reranker_model_name,
            )
            logger.info(
                "RerankerAdapter を生成: model=%s",
                self.config.reranker_model_name,
            )
        return self._reranker

    def create_dataloader(self) -> PDFLoaderAdapter:
        """DataLoaderPort の具体実装を生成する。"""
        if self._dataloader is None:
            self._dataloader = PDFLoaderAdapter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                block_max_bytes=self.config.block_max_bytes,
            )
            logger.info("PDFLoaderAdapter を生成")
        return self._dataloader

    def create_workflow(self) -> AgentWorkflow:
        """AgentWorkflow を生成する。"""
        if self._workflow is None:
            self._workflow = AgentWorkflow(
                llm=self.create_llm(),
                vectorstore=self.create_vectorstore(),
                reranker=self.create_reranker(),
                config=self.config,
            )
            logger.info("AgentWorkflow を生成")
        return self._workflow

    def create_ingestion(self) -> DataIngestion:
        """DataIngestion を生成する。"""
        if self._ingestion is None:
            self._ingestion = DataIngestion(
                loader=self.create_dataloader(),
                vectorstore=self.create_vectorstore(),
            )
            logger.info("DataIngestion を生成")
        return self._ingestion

    def create_ui(self) -> GradioHandler:
        """GradioHandler を生成する。"""
        return GradioHandler(
            ingestion=self.create_ingestion(),
            config=self.config,
            llm=self.create_llm(),
            vectorstore=self.create_vectorstore(),
            reranker=self.create_reranker(),
        )
