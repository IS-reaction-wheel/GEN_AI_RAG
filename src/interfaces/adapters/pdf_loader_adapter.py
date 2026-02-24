"""PDF データローダーアダプタ（DataLoaderPort の実装）"""

from __future__ import annotations

import logging
import re
import unicodedata
import uuid

from domain.models import DocumentChunk

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# テキスト前処理（純粋関数）
# ---------------------------------------------------------------------------


def clean_pdf_text(text: str) -> str:
    """PDF から抽出したテキストのノイズを除去する。

    - 1文字行が3行以上連続するブロックを除去
    - 3行以上の連続空行を2行に圧縮
    """
    # 1文字行が3行以上連続するブロックを除去
    lines = text.split("\n")
    cleaned_lines: list[str] = []
    single_char_buffer: list[str] = []

    for line in lines:
        stripped = line.strip()
        if len(stripped) == 1:
            single_char_buffer.append(line)
        else:
            if len(single_char_buffer) < 3:
                cleaned_lines.extend(single_char_buffer)
            single_char_buffer = []
            cleaned_lines.append(line)

    # 末尾のバッファ処理
    if len(single_char_buffer) < 3:
        cleaned_lines.extend(single_char_buffer)

    result = "\n".join(cleaned_lines)

    # 3行以上の連続空行を2行に圧縮
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result


def split_into_safe_blocks(
    text: str,
    max_bytes: int = 40000,
    overlap_chars: int = 100,
) -> list[str]:
    """spaCy のバイト制限対策でテキストを段落区切りで分割する。"""
    if len(text.encode("utf-8")) <= max_bytes:
        return [text]

    paragraphs = text.split("\n\n")
    blocks: list[str] = []
    current_block: list[str] = []
    current_bytes = 0

    for para in paragraphs:
        para_bytes = len(para.encode("utf-8"))

        if current_bytes + para_bytes > max_bytes and current_block:
            block_text = "\n\n".join(current_block)
            blocks.append(block_text)

            # オーバーラップ: 最後のブロックの末尾を次のブロックの先頭に含める
            overlap_text = block_text[-overlap_chars:] if overlap_chars > 0 else ""
            current_block = []
            current_bytes = 0
            if overlap_text:
                current_block.append(overlap_text)
                current_bytes = len(overlap_text.encode("utf-8"))

        current_block.append(para)
        current_bytes += para_bytes

    if current_block:
        blocks.append("\n\n".join(current_block))

    return blocks


_nlp_instance = None


def _get_nlp():
    """spaCy 日本語モデルを遅延ロードしてキャッシュする。"""
    global _nlp_instance  # noqa: PLW0603
    if _nlp_instance is None:
        import spacy

        try:
            _nlp_instance = spacy.load("ja_ginza", disable=["parser", "ner"])
        except OSError:
            logger.warning(
                "spaCy 日本語モデルが見つかりません。空白分割にフォールバックします。"
            )
    return _nlp_instance


def tokenize(text: str) -> list[str]:
    """BM25 用の形態素解析トークナイズ。

    spaCy (ja_ginza) で形態素解析し、名詞・動詞・形容詞・固有名詞・数詞の
    見出し語を抽出する。ストップワードと単文字ノイズは除外する。
    モデルは初回呼び出し時に1度だけロードされる。
    """
    nlp = _get_nlp()
    if nlp is None:
        return text.split()

    doc = nlp(text)
    target_pos = {"NOUN", "VERB", "ADJ", "PROPN", "NUM"}
    tokens: list[str] = []
    for token in doc:
        if token.pos_ not in target_pos:
            continue
        if token.is_stop:
            continue
        lemma = token.lemma_
        if len(lemma) == 1 and re.match(r"[ぁ-ん\u30fc!-/:-@\[-`{-~]", lemma):
            continue
        tokens.append(lemma)
    return tokens


# ---------------------------------------------------------------------------
# PDFLoaderAdapter
# ---------------------------------------------------------------------------


class PDFLoaderAdapter:
    """markitdown + spaCy による DataLoaderPort の具体実装"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        block_max_bytes: int = 40000,
    ) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._block_max_bytes = block_max_bytes

    def load(self, file_path: str) -> list[DocumentChunk]:
        """PDF からテキストを抽出しチャンク分割して返す"""
        from pathlib import Path

        from markitdown import MarkItDown

        source = Path(file_path).name
        logger.info("PDF 読み込み開始: %s", source)

        md = MarkItDown()
        result = md.convert(file_path)
        raw_text = result.text_content

        # 前処理
        cleaned = unicodedata.normalize("NFKC", raw_text)
        cleaned = clean_pdf_text(cleaned)
        blocks = split_into_safe_blocks(cleaned, max_bytes=self._block_max_bytes)

        # チャンク分割
        all_chunks: list[DocumentChunk] = []
        for block in blocks:
            chunks = self._split_text(block, source)
            all_chunks.extend(chunks)

        logger.info("チャンク分割完了: %d チャンク", len(all_chunks))
        return all_chunks

    def _split_text(
        self,
        text: str,
        source: str,
    ) -> list[DocumentChunk]:
        """SpacyTextSplitter で文境界を考慮してチャンク分割する。"""
        from langchain_text_splitters import SpacyTextSplitter

        splitter = SpacyTextSplitter(
            separator="\n\n",
            pipeline="ja_ginza",
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
        )
        split_texts = splitter.split_text(text)

        chunks: list[DocumentChunk] = []
        for t in split_texts:
            stripped = t.strip()
            if stripped:
                chunks.append(
                    DocumentChunk(
                        chunk_id=str(uuid.uuid4()),
                        text=stripped,
                        source=source,
                    ),
                )
        return chunks
