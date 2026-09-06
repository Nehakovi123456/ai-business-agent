import os
from typing import List, Dict, Any
from pathlib import Path

from langchain_core.documents import Document
from src.config import CHROMA_PERSIST_DIR, OPENAI_API_KEY, GEMINI_API_KEY

_embeddings_cache = None

def get_embeddings():
    """Initializes embeddings model with fallback options."""
    global _embeddings_cache
    if _embeddings_cache is not None:
        return _embeddings_cache

    # 1. Try HuggingFace / SentenceTransformers (Free, local, fast)
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        _embeddings_cache = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        print("[VectorStore] Using HuggingFace all-MiniLM-L6-v2 embeddings.")
        return _embeddings_cache
    except Exception as e:
        print(f"[VectorStore] HuggingFace embeddings init failed: {e}")

    # 2. Try OpenAI Embeddings if key present
    if OPENAI_API_KEY:
        try:
            from langchain_openai import OpenAIEmbeddings
            _embeddings_cache = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
            return _embeddings_cache
        except Exception as e:
            print(f"[VectorStore] OpenAI embeddings init failed: {e}")

    # 3. Fallback dummy embeddings wrapper for local testing without sentence-transformers
    from langchain_core.embeddings import Embeddings
    class SimpleHashEmbeddings(Embeddings):
        def embed_documents(self, texts: List[str]) -> List[List[float]]:
            return [[float(hash(t) % 100) / 100.0] * 384 for t in texts]
        def embed_query(self, text: str) -> List[float]:
            return [float(hash(text) % 100) / 100.0] * 384

    _embeddings_cache = SimpleHashEmbeddings()
    print("[VectorStore] Using SimpleHash fallback embeddings.")
    return _embeddings_cache

class VectorDBManager:
    def __init__(self, collection_name: str = "company_documents"):
        self.collection_name = collection_name
        self.persist_dir = str(CHROMA_PERSIST_DIR)
        self.embeddings = get_embeddings()
        self.vectorstore = None
        self._init_store()

    def _init_store(self):
        try:
            from langchain_community.vectorstores import Chroma
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_dir
            )
        except Exception as e:
            print(f"[VectorStore] Chroma DB init error: {e}")

    def add_documents(self, documents: List[Document]):
        """Indexes documents into ChromaDB."""
        if not documents:
            return
        if self.vectorstore:
            self.vectorstore.add_documents(documents)
            try:
                if hasattr(self.vectorstore, "persist"):
                    self.vectorstore.persist()
            except Exception:
                pass
            print(f"[VectorStore] Added {len(documents)} document chunks to {self.collection_name}.")

    def reset_collection(self):
        """Clears all documents from ChromaDB collection to isolate user company uploads."""
        if self.vectorstore:
            try:
                all_ids = self.vectorstore.get().get("ids", [])
                if all_ids:
                    self.vectorstore.delete(ids=all_ids)
                if hasattr(self.vectorstore, "persist"):
                    self.vectorstore.persist()
                print(f"[VectorStore] Cleared {len(all_ids)} document chunks from collection.")
                return len(all_ids)
            except Exception as e:
                print(f"[VectorStore] Reset collection error: {e}")
                return 0
        return 0

    def search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Performs similarity search and returns structured results with citation metadata."""
        if not self.vectorstore:
            return []

        try:
            results = self.vectorstore.similarity_search_with_score(query, k=top_k)
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "filename": doc.metadata.get("filename", "Unknown Document"),
                    "page_number": doc.metadata.get("page_number", 1),
                    "chunk_id": doc.metadata.get("chunk_id", "N/A"),
                    "relevance_score": round(float(score), 4)
                })
            return formatted_results
        except Exception as e:
            print(f"[VectorStore] Search error: {e}")
            try:
                docs = self.vectorstore.similarity_search(query, k=top_k)
                formatted_results = []
                for doc in docs:
                    formatted_results.append({
                        "content": doc.page_content,
                        "filename": doc.metadata.get("filename", "Unknown Document"),
                        "page_number": doc.metadata.get("page_number", 1),
                        "chunk_id": doc.metadata.get("chunk_id", "N/A"),
                        "relevance_score": 0.85
                    })
                return formatted_results
            except Exception as e2:
                print(f"[VectorStore] Fallback search error: {e2}")
                return []

    def get_document_count(self) -> int:
        """Returns total document count in collection."""
        if self.vectorstore:
            try:
                return self.vectorstore._collection.count()
            except Exception:
                try:
                    res = self.vectorstore.get()
                    if res and "ids" in res:
                        return len(res["ids"])
                except Exception as e:
                    print(f"[VectorStore] get_document_count error: {e}")
        return 0
