"""Runner script to index KB and generate verification transcripts for T2 and T3."""

import os
import sys
import re

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag.indexing import VectorIndexManager, KB_DIRECTORY


def verify_kb_docs():
    files = sorted([f for f in os.listdir(KB_DIRECTORY) if f.endswith(".md")])
    lines = [
        "=" * 70,
        "NAUKRI.COM KNOWLEDGE BASE MANIFEST (TASK T2)",
        "=" * 70,
        f"Total KB Documents: {len(files)} (Requirement: 12)",
        "",
        f"{'Filename':30s} | {'Topic':32s} | {'Sentences':9s} | {'Status'}",
        "-" * 85,
    ]
    for f in files:
        p = os.path.join(KB_DIRECTORY, f)
        with open(p, "r", encoding="utf-8") as fh:
            content = fh.read().strip()
        lines_raw = [l.strip() for l in content.splitlines() if not l.strip().startswith("#") and l.strip()]
        body = " ".join(lines_raw)
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
        topic = content.splitlines()[0].lstrip("#").strip() if content else f
        status = "VALID (2-5)" if 2 <= len(sentences) <= 5 else "INVALID"
        lines.append(f"{f:30s} | {topic[:32]:32s} | {len(sentences):9d} | {status}")

    lines.append("=" * 70)
    out = "\n".join(lines)
    print(out)
    with open("transcripts/t2_kb_manifest.txt", "w", encoding="utf-8") as fh:
        fh.write(out + "\n")


def index_and_sample():
    manager = VectorIndexManager()
    stats = manager.index_all()
    print("\nIndexing Complete:")
    print(f"  - kb_fixed_overlap: {stats['kb_fixed_overlap']} chunks indexed")
    print(f"  - kb_sentence_based: {stats['kb_sentence_based']} chunks indexed")

    sample_query = "What is the policy on notice period buyout and early release?"
    fixed_results = manager.query("kb_fixed_overlap", sample_query, top_k=2)
    sentence_results = manager.query("kb_sentence_based", sample_query, top_k=2)

    lines = [
        "=" * 70,
        "CHROMADB DUAL CHUNKING INDEXING & RETRIEVAL SAMPLE (TASK T3)",
        "=" * 70,
        f"Sample Query: '{sample_query}'",
        f"Total Chunks - Fixed Overlap: {stats['kb_fixed_overlap']}",
        f"Total Chunks - Sentence Based: {stats['kb_sentence_based']}",
        "",
        "--- COLLECTION 1: kb_fixed_overlap (Top 2 Chunks) ---",
    ]
    for i, r in enumerate(fixed_results, 1):
        lines.append(f"[{i}] Chunk ID: {r['chunk_id']} | Parent: {r['parent_doc_id']} | Sim: {r['cosine_similarity']:.4f}")
        lines.append(f"    Text: {r['text'][:120]}...")

    lines.extend([
        "",
        "--- COLLECTION 2: kb_sentence_based (Top 2 Chunks) ---",
    ])
    for i, r in enumerate(sentence_results, 1):
        lines.append(f"[{i}] Chunk ID: {r['chunk_id']} | Parent: {r['parent_doc_id']} | Sim: {r['cosine_similarity']:.4f}")
        lines.append(f"    Text: {r['text'][:120]}...")

    lines.append("=" * 70)
    out = "\n".join(lines)
    print("\n" + out)
    with open("transcripts/t3_indexing_sample.txt", "w", encoding="utf-8") as fh:
        fh.write(out + "\n")


if __name__ == "__main__":
    verify_kb_docs()
    index_and_sample()
