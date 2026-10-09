"""Unit tests for RAG chunking, indexing, and calibrated generation (Tasks T3, T4, T5)."""

import pytest
from rag.chunking import FixedOverlapChunker, SentenceChunker
from rag.indexing import VectorIndexManager
from rag.generate import GroundedGenerator, FALLBACK_REFUSAL_TEXT


def test_fixed_overlap_chunking():
    chunker = FixedOverlapChunker(chunk_size=200, overlap=40)
    sample_text = "This is a sentence about hiring policy. " * 10
    chunks = chunker.chunk_document("test.md", "Test Topic", sample_text)
    assert len(chunks) > 1
    assert chunks[0].strategy == "fixed_overlap"
    assert chunks[0].parent_doc_id == "test.md"


def test_sentence_chunking():
    chunker = SentenceChunker()
    sample_text = "# Policy\n\nFirst sentence. Second sentence! Third sentence?"
    chunks = chunker.chunk_document("test.md", "Policy", sample_text)
    assert len(chunks) == 3
    assert chunks[0].strategy == "sentence_based"
    assert "First sentence." in chunks[0].text


def test_indexing_and_dual_retrieval():
    mgr = VectorIndexManager()
    hits_fixed = mgr.query("kb_fixed_overlap", "notice period buyout", top_k=2)
    hits_sent = mgr.query("kb_sentence_based", "notice period buyout", top_k=2)

    assert len(hits_fixed) > 0
    assert len(hits_sent) > 0
    assert 0.0 <= hits_fixed[0]["cosine_similarity"] <= 1.0
    assert 0.0 <= hits_sent[0]["cosine_similarity"] <= 1.0


def test_calibrated_threshold():
    gen = GroundedGenerator()
    thresh = gen.calibrate_threshold()
    assert 0.35 <= thresh <= 0.60
    assert gen.calibration_details["min_in_scope"] > gen.calibration_details["max_out_of_scope"]


def test_grounded_answer_and_fallback():
    gen = GroundedGenerator()
    gen.calibrate_threshold()

    # In scope query
    res_in = gen.generate_grounded_answer("What is the notice period policy?")
    assert res_in["grounded"] is True
    assert "05_notice_period.md" in res_in["citations"]

    # Out of scope query
    res_out = gen.generate_grounded_answer("What is the lunch menu in the corporate cafeteria?")
    assert res_out["grounded"] is False
    assert res_out["answer"] == FALLBACK_REFUSAL_TEXT
