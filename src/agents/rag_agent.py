from src.graph.state import AgentState
from src.tools.rag_tool import query_internal_documents
from src.db.database import log_agent_activity

def rag_agent(state: AgentState) -> AgentState:
    """
    RAG / Document Agent:
    Extracts relevant passages from internal company reports, PDFs, CSVs, and sales data.
    """
    query = state["query_text"]
    query_id = state.get("query_id", 0)

    # Search internal vector store
    rag_chunks = query_internal_documents(query, top_k=4)

    log_summary = f"Retrieved {len(rag_chunks)} internal document passages with citation metadata."
    log_agent_activity(query_id, "RAG Agent", "COMPLETED", log_summary)

    new_logs = list(state.get("activity_logs", []))
    new_logs.append({
        "agent": "RAG Agent",
        "status": "✓ Completed",
        "detail": log_summary
    })

    return {
        **state,
        "current_step": "Internal Documents Analyzed",
        "rag_data": rag_chunks,
        "activity_logs": new_logs
    }
