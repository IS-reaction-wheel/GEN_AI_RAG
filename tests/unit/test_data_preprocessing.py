"""データ前処理（純粋関数）のユニットテスト"""

from interfaces.adapters.pdf_loader_adapter import (
    clean_pdf_text,
    split_into_safe_blocks,
)


class TestCleanPdfText:
    """PDF テキストクリーニングのテスト"""

    def test_removes_single_char_line_blocks(self) -> None:
        """1文字行が3行以上連続するブロックが除去されることを検証する。"""
        text = "正常なテキスト\nあ\nい\nう\n正常なテキスト"
        result = clean_pdf_text(text)
        assert "あ\nい\nう" not in result
        assert "正常なテキスト" in result

    def test_keeps_short_single_char_lines(self) -> None:
        """1文字行が2行以下の場合は保持されることを検証する。"""
        text = "正常\nあ\nい\n正常"
        result = clean_pdf_text(text)
        assert "あ\nい" in result

    def test_compresses_excessive_blank_lines(self) -> None:
        """3行以上の連続空行が2行に圧縮されることを検証する。"""
        text = "段落1\n\n\n\n\n段落2"
        result = clean_pdf_text(text)
        assert "\n\n\n" not in result
        assert "段落1\n\n段落2" == result

    def test_preserves_normal_text(self) -> None:
        """正常なテキストが変更されないことを検証する。"""
        text = "これは正常なテキストです。\n\n次の段落です。"
        result = clean_pdf_text(text)
        assert result == text

    def test_empty_text(self) -> None:
        """空文字列が変更されないことを検証する。"""
        assert clean_pdf_text("") == ""


class TestSplitIntoSafeBlocks:
    """spaCy バイト制限対策ブロック分割のテスト"""

    def test_short_text_returns_single_block(self) -> None:
        """短いテキストが分割されないことを検証する。"""
        text = "短いテキスト"
        blocks = split_into_safe_blocks(text, max_bytes=40000)
        assert len(blocks) == 1
        assert blocks[0] == text

    def test_long_text_splits(self) -> None:
        """長いテキストが分割されることを検証する。"""
        # 1文字あたり3バイト（UTF-8 日本語）→ 7000文字 ≈ 21000バイト
        para = "あ" * 7000
        text = f"{para}\n\n{para}\n\n{para}"
        blocks = split_into_safe_blocks(text, max_bytes=25000)
        assert len(blocks) >= 2

    def test_blocks_have_overlap(self) -> None:
        """分割されたブロック間にオーバーラップがあることを検証する。"""
        para = "あ" * 7000
        text = f"{para}\n\n{para}\n\n{para}"
        blocks = split_into_safe_blocks(text, max_bytes=25000, overlap_chars=100)
        if len(blocks) >= 2:
            # 2番目のブロックの先頭に1番目のブロックの末尾が含まれる
            assert blocks[0][-50:] in blocks[1]

    def test_empty_text(self) -> None:
        """空文字列が1ブロックとして返されることを検証する。"""
        blocks = split_into_safe_blocks("", max_bytes=40000)
        assert len(blocks) == 1
