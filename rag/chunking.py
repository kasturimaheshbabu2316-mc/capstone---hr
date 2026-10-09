"""Dual Chunking Strategies for Knowledge Base Policy Documents.

Track: Recruitment & HR (Naukri.com)
Part 1 - Task T3: Chunking Strategies
Strategy A: Fixed-size chunking (200 characters with 40-character sliding overlap)
Strategy B: Sentence-based syntactic splitting
"""

from typing import Dict, List
import re
from pydantic import BaseModel, Field


class Chunk(BaseModel):
    chunk_id: str
    text: str
    parent_doc_id: str
    topic_name: str
    chunk_index: int
    char_start: int
    char_end: int
    strategy: str


class FixedOverlapChunker:
    """Strategy A: Fixed-size chunking with sliding overlap.

    Chunk size: 200 characters
    Overlap: 40 characters
    Step: 160 characters
    """

    def __init__(self, chunk_size: int = 200, overlap: int = 40):
        if overlap >= chunk_size:
            raise ValueError("Overlap must be strictly less than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.step = chunk_size - overlap

    def chunk_document(self, parent_doc_id: str, topic_name: str, content: str) -> List[Chunk]:
        clean_text = content.strip()
        chunks: List[Chunk] = []
        text_len = len(clean_text)

        if text_len == 0:
            return chunks

        if text_len <= self.chunk_size:
            chunks.append(
                Chunk(
                    chunk_id=f"{parent_doc_id}_fixed_0",
                    text=clean_text,
                    parent_doc_id=parent_doc_id,
                    topic_name=topic_name,
                    chunk_index=0,
                    char_start=0,
                    char_end=text_len,
                    strategy="fixed_overlap",
                )
            )
            return chunks

        start = 0
        idx = 0
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk_slice = clean_text[start:end].strip()
            if chunk_slice:
                chunks.append(
                    Chunk(
                        chunk_id=f"{parent_doc_id}_fixed_{idx}",
                        text=chunk_slice,
                        parent_doc_id=parent_doc_id,
                        topic_name=topic_name,
                        chunk_index=idx,
                        char_start=start,
                        char_end=end,
                        strategy="fixed_overlap",
                    )
                )
                idx += 1
            if end >= text_len:
                break
            start += self.step

        return chunks


class SentenceChunker:
    """Strategy B: Sentence-based syntactic boundary splitting."""

    def __init__(self):
        # Regular expression for sentence boundaries (. ! ?)
        self.sentence_regex = re.compile(r"(?<=[.!?])\s+")

    def chunk_document(self, parent_doc_id: str, topic_name: str, content: str) -> List[Chunk]:
        # Strip header lines starting with #
        lines = [line.strip() for line in content.splitlines() if not line.strip().startswith("#")]
        body = " ".join([l for l in lines if l]).strip()

        chunks: List[Chunk] = []
        if not body:
            return chunks

        raw_sentences = [s.strip() for s in self.sentence_regex.split(body) if s.strip()]
        
        current_pos = 0
        for idx, sentence in enumerate(raw_sentences):
            start = content.find(sentence, current_pos)
            if start == -1:
                start = current_pos
            end = start + len(sentence)
            current_pos = end

            chunks.append(
                Chunk(
                    chunk_id=f"{parent_doc_id}_sent_{idx}",
                    text=sentence,
                    parent_doc_id=parent_doc_id,
                    topic_name=topic_name,
                    chunk_index=idx,
                    char_start=start,
                    char_end=end,
                    strategy="sentence_based",
                )
            )

        return chunks
