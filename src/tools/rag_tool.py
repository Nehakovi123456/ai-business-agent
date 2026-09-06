from typing import List, Dict, Any
from src.rag.vectorstore import VectorDBManager

def query_internal_documents(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """
    Searches internal company documents via ChromaDB vector store.
    Returns matching passages with source citations and metadata.
    Enforces strict knowledge base isolation without fabricating missing company facts.
    """
    db_manager = VectorDBManager()
    doc_count = db_manager.get_document_count()
    
    # 1. Search active user documents if present in vector storage
    if doc_count > 0:
        results = db_manager.search(query, top_k=top_k)
        if results:
            for r in results:
                # Mark retrieved text clearly as Source Fact
                r["is_user_knowledge_base"] = True
            return results

    # 2. Honest status if no user document is indexed in current knowledge base
    return [
        {
            "content": f"[NO MATCHING USER DOCUMENT]: No active company document chunk found in ChromaDB vector memory for query: '{query[:65]}'. Internal company metrics are marked as [ASSUMPTION] or [AI INFERENCE].",
            "filename": "Knowledge Base Memory Status",
            "page_number": 1,
            "chunk_id": "no_matching_user_doc",
            "relevance_score": 0.0,
            "is_user_knowledge_base": False
        }
    ]
