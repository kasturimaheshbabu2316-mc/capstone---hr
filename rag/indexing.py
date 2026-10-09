"""ChromaDB Vector Indexing for Dual Chunking Collections.

Track: Recruitment & HR (Naukri.com)
Part 1 - Task T3: ChromaDB Collections Management
Collections:
  - kb_fixed_overlap
  - kb_sentence_based
Embeddings: Offline all-MiniLM-L6-v2 via SentenceTransformers
"""

import os
from typing import Dict, List, Optional, Tuple
import chromadb
from sentence_transformers import SentenceTransformer

from rag.chunking import Chunk, FixedOverlapChunker, SentenceChunker

KB_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kb"))
CHROMA_PERSIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))

# Model is cached locally for offline execution
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
_model_instance: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    global _model_instance
    if _model_instance is None:
        _model_instance = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model_instance


class VectorIndexManager:
    """Manages two ChromaDB collections populated via upsert()."""

    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR):
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.model = get_embedding_model()

        # Create or fetch dual collections with cosine distance space
        self.fixed_collection = self.client.get_or_create_collection(
            name="kb_fixed_overlap",
            metadata={"hnsw:space": "cosine"}
        )
        self.sentence_collection = self.client.get_or_create_collection(
            name="kb_sentence_based",
            metadata={"hnsw:space": "cosine"}
        )

    def load_kb_documents(self, kb_dir: str = KB_DIRECTORY) -> List[Tuple[str, str, str]]:
        """Loads all .md files in the kb/ directory.
        
        Returns: List of (parent_doc_id, topic_name, text_content)
        """
        docs: List[Tuple[str, str, str]] = []
        if not os.path.exists(kb_dir):
            return docs

        for fname in sorted(os.listdir(kb_dir)):
            if fname.endswith(".md"):
                doc_path = os.path.join(kb_dir, fname)
                with open(doc_path, "r", encoding="utf-8") as fh:
                    content = fh.read().strip()
                
                # Extract topic name from first Markdown header line
                first_line = content.splitlines()[0] if content else fname
                topic_name = first_line.lstrip("#").strip()
                docs.append((fname, topic_name, content))

        return docs

    def index_all(self, kb_dir: str = KB_DIRECTORY) -> Dict[str, int]:
        """Indexes all KB documents into both collections using upsert()."""
        raw_docs = self.load_kb_documents(kb_dir)
        fixed_chunker = FixedOverlapChunker(chunk_size=200, overlap=40)
        sentence_chunker = SentenceChunker()

        all_fixed_chunks: List[Chunk] = []
        all_sentence_chunks: List[Chunk] = []

        for doc_id, topic, content in raw_docs:
            all_fixed_chunks.extend(fixed_chunker.chunk_document(doc_id, topic, content))
            all_sentence_chunks.extend(sentence_chunker.chunk_document(doc_id, topic, content))

        # Index into Strategy A: kb_fixed_overlap
        if all_fixed_chunks:
            fixed_texts = [c.text for c in all_fixed_chunks]
            fixed_embeddings = self.model.encode(fixed_texts, normalize_embeddings=True).tolist()
            fixed_ids = [c.chunk_id for c in all_fixed_chunks]
            fixed_metadatas = [
                {
                    "parent_doc_id": c.parent_doc_id,
                    "topic_name": c.topic_name,
                    "chunk_index": c.chunk_index,
                    "strategy": c.strategy,
                }
                for c in all_fixed_chunks
            ]
            self.fixed_collection.upsert(
                ids=fixed_ids,
                documents=fixed_texts,
                embeddings=fixed_embeddings,
                metadatas=fixed_metadatas,
            )

        # Index into Strategy B: kb_sentence_based
        if all_sentence_chunks:
            sentence_texts = [c.text for c in all_sentence_chunks]
            sentence_embeddings = self.model.encode(sentence_texts, normalize_embeddings=True).tolist()
            sentence_ids = [c.chunk_id for c in all_sentence_chunks]
            sentence_metadatas = [
                {
                    "parent_doc_id": c.parent_doc_id,
                    "topic_name": c.topic_name,
                    "chunk_index": c.chunk_index,
                    "strategy": c.strategy,
                }
                for c in all_sentence_chunks
            ]
            self.sentence_collection.upsert(
                ids=sentence_ids,
                documents=sentence_texts,
                embeddings=sentence_embeddings,
                metadatas=sentence_metadatas,
            )

        return {
            "kb_fixed_overlap": len(all_fixed_chunks),
            "kb_sentence_based": len(all_sentence_chunks),
        }

    def add_document(self, filename: str, content: str) -> Dict[str, int]:
        """Dynamically adds/updates a single document across both collections (for POST /add-document)."""
        first_line = content.splitlines()[0] if content else filename
        topic_name = first_line.lstrip("#").strip()

        fixed_chunker = FixedOverlapChunker(chunk_size=200, overlap=40)
        sentence_chunker = SentenceChunker()

        fixed_chunks = fixed_chunker.chunk_document(filename, topic_name, content)
        sent_chunks = sentence_chunker.chunk_document(filename, topic_name, content)

        if fixed_chunks:
            f_texts = [c.text for c in fixed_chunks]
            f_embs = self.model.encode(f_texts, normalize_embeddings=True).tolist()
            f_ids = [c.chunk_id for c in fixed_chunks]
            f_metas = [
                {
                    "parent_doc_id": c.parent_doc_id,
                    "topic_name": c.topic_name,
                    "chunk_index": c.chunk_index,
                    "strategy": c.strategy,
                }
                for c in fixed_chunks
            ]
            self.fixed_collection.upsert(ids=f_ids, documents=f_texts, embeddings=f_embs, metadatas=f_metas)

        if sent_chunks:
            s_texts = [c.text for c in sent_chunks]
            s_embs = self.model.encode(s_texts, normalize_embeddings=True).tolist()
            s_ids = [c.chunk_id for c in sent_chunks]
            s_metas = [
                {
                    "parent_doc_id": c.parent_doc_id,
                    "topic_name": c.topic_name,
                    "chunk_index": c.chunk_index,
                    "strategy": c.strategy,
                }
                for c in sent_chunks
            ]
            self.sentence_collection.upsert(ids=s_ids, documents=s_texts, embeddings=s_embs, metadatas=s_metas)

        return {
            "fixed_chunks_added": len(fixed_chunks),
            "sentence_chunks_added": len(sent_chunks),
        }

    def query(self, collection_name: str, query_text: str, top_k: int = 3) -> List[Dict]:
        """Queries the specified collection and returns chunks with cosine similarity.
        
        Chroma with hnsw:space=cosine returns distance in [0, 2].
        Cosine similarity = 1.0 - distance.
        """
        if collection_name == "kb_fixed_overlap":
            coll = self.fixed_collection
        elif collection_name == "kb_sentence_based":
            coll = self.sentence_collection
        else:
            raise ValueError(f"Unknown collection: {collection_name}")

        query_emb = self.model.encode([query_text], normalize_embeddings=True).tolist()
        results = coll.query(
            query_embeddings=query_emb,
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        hits: List[Dict] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return hits

        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        for chunk_id, doc, meta, dist in zip(ids, docs, metas, dists):
            # Convert cosine distance to cosine similarity
            sim = float(max(0.0, min(1.0, 1.0 - dist)))
            hits.append({
                "chunk_id": chunk_id,
                "text": doc,
                "parent_doc_id": meta.get("parent_doc_id", "unknown"),
                "topic_name": meta.get("topic_name", "unknown"),
                "chunk_index": meta.get("chunk_index", 0),
                "strategy": meta.get("strategy", collection_name),
                "distance": float(dist),
                "cosine_similarity": round(sim, 4),
            })

        return hits
