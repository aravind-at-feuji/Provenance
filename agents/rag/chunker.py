"""
agents/rag/chunker.py — Recursive semantic text chunker.

Architecture reference: §K.2 Pipeline, §K.3 Metadata on Every Chunk.
Requirements:
  - Target ~500 tokens (~2000 characters)
  - ~15% overlap (~75 tokens / 300 characters)
  - Never split across section boundaries
  - Preserves hierarchical section_path for citations (e.g., 'Article IV > Paragraph 2')
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChunkData:
    """A semantic text chunk with its provenance metadata."""

    chunk_index: int
    content: str
    section_path: str | None
    token_count: int
    metadata: dict[str, Any] = field(default_factory=dict)


class RecursiveSemanticChunker:
    """
    Recursively segments structured regulatory documents and contracts into semantic chunks.
    """

    HEADING_REGEX = re.compile(
        r"^(?:#{1,4}\s+|[A-Z0-9\.\s]{2,15}:|Section\s+\d+|Article\s+[IVXLCDM\d]+|PART\s+[A-Z0-9]+)\s*(.*)$",
        re.MULTILINE,
    )

    def __init__(
        self,
        target_tokens: int = 500,
        overlap_pct: float = 0.15,
        approx_chars_per_token: int = 4,
    ) -> None:
        self.target_tokens = target_tokens
        self.overlap_pct = overlap_pct
        self.approx_chars_per_token = approx_chars_per_token
        self.target_chars = target_tokens * approx_chars_per_token
        self.overlap_chars = int(self.target_chars * overlap_pct)

    def chunk_document(
        self,
        text: str,
        initial_section_path: str | None = None,
        base_metadata: dict[str, Any] | None = None,
    ) -> list[ChunkData]:
        """
        Split text into overlapping semantic chunks while preserving section boundaries.
        """
        if not text or not text.strip():
            return []

        # Split into major sections first based on headings
        sections = self._split_by_headings(text, initial_section_path)
        chunks: list[ChunkData] = []
        global_idx = 0

        for sec_path, sec_text in sections:
            # Further split section by paragraphs
            sec_chunks = self._chunk_section_text(sec_text, sec_path, global_idx, base_metadata or {})
            chunks.extend(sec_chunks)
            global_idx += len(sec_chunks)

        return chunks

    def _split_by_headings(
        self, text: str, default_path: str | None
    ) -> list[tuple[str | None, str]]:
        """Split document text on heading boundaries."""
        matches = list(self.HEADING_REGEX.finditer(text))
        if not matches:
            return [(default_path, text)]

        sections: list[tuple[str | None, str]] = []
        current_pos = 0
        current_heading = default_path

        for match in matches:
            heading_pos = match.start()
            if heading_pos > current_pos:
                content = text[current_pos:heading_pos].strip()
                if content:
                    sections.append((current_heading, content))
            current_heading = match.group(0).strip().lstrip("#").strip()
            current_pos = heading_pos

        # Remainder
        if current_pos < len(text):
            content = text[current_pos:].strip()
            if content:
                sections.append((current_heading, content))

        return sections if sections else [(default_path, text)]

    def _chunk_section_text(
        self,
        text: str,
        section_path: str | None,
        start_index: int,
        base_meta: dict[str, Any],
    ) -> list[ChunkData]:
        """Chunk text within a section using paragraph / sentence boundaries with overlap."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [text.strip()]

        chunks: list[ChunkData] = []
        current_buffer: list[str] = []
        current_len = 0
        chunk_idx = start_index

        for para in paragraphs:
            para_len = len(para)

            # If adding paragraph exceeds target chars and buffer is not empty
            if current_len + para_len > self.target_chars and current_buffer:
                chunk_str = "\n\n".join(current_buffer)
                token_count = max(1, len(chunk_str) // self.approx_chars_per_token)
                chunks.append(
                    ChunkData(
                        chunk_index=chunk_idx,
                        content=chunk_str,
                        section_path=section_path,
                        token_count=token_count,
                        metadata=dict(base_meta),
                    )
                )
                chunk_idx += 1

                # Carry over overlap from the end of current_buffer
                overlap_text = chunk_str[-self.overlap_chars :] if len(chunk_str) > self.overlap_chars else ""
                current_buffer = [overlap_text, para] if overlap_text else [para]
                current_len = sum(len(p) for p in current_buffer)
            else:
                current_buffer.append(para)
                current_len += para_len

        # Flush remaining buffer
        if current_buffer:
            chunk_str = "\n\n".join(current_buffer).strip()
            if chunk_str:
                token_count = max(1, len(chunk_str) // self.approx_chars_per_token)
                chunks.append(
                    ChunkData(
                        chunk_index=chunk_idx,
                        content=chunk_str,
                        section_path=section_path,
                        token_count=token_count,
                        metadata=dict(base_meta),
                    )
                )

        return chunks
