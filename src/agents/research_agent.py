from src.graph.state import AgentState
from src.tools.search_tool import search_web
from src.db.database import log_agent_activity

def research_agent(state: AgentState) -> AgentState:
    """
    Research Agent:
    Performs external market research on trends, regulations, size, and growth drivers.
    """
    query = state["query_text"]
    query_id = state.get("query_id", 0)

    # Perform web research
    search_results = search_web(f"{query} market size growth trends pricing 2025")
    
    log_summary = f"Retrieved {len(search_results)} external market intelligence sources."
    log_agent_activity(query_id, "Research Agent", "COMPLETED", log_summary)

    new_logs = list(state.get("activity_logs", []))
    new_logs.append({
        "agent": "Research Agent",
        "status": "✓ Completed",
        "detail": log_summary
    })

    return {
        **state,
        "current_step": "Research Gathered",
        "research_data": search_results,
        "activity_logs": new_logs
    }
