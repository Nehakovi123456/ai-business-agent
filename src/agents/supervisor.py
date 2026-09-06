from src.graph.state import AgentState
from src.config import get_llm
from src.db.database import log_agent_activity

def supervisor_agent(state: AgentState) -> AgentState:
    """
    Supervisor / Orchestrator Agent:
    Decomposes the business inquiry into specific agent tasks and plans workflow routing.
    """
    query = state["query_text"]
    query_id = state.get("query_id", 0)
    llm = get_llm(state.get("llm_provider"))

    prompt = f"""
    You are the Supervisor Orchestrator of an AI Business Intelligence System.
    Analyze the user's business query: "{query}"

    Decompose this problem into strategic steps for our specialized agents:
    1. Research Agent: External market trends, industry size, regulations.
    2. RAG Agent: Internal document retrieval (annual reports, sales, production capacity).
    3. Competitor Agent: Target competitors, pricing benchmark, features.
    4. Analysis Agent: Financial opportunity, risk matrix, sensitivity score.
    5. Fact-Checker Agent: Claim verification & evidence audit.
    6. Report Agent: Final business feasibility report synthesis.

    Return a concise 6-step execution plan.
    """

    plan_steps = [
        "1. External Market & Regulatory Research",
        "2. Internal Company Document RAG Retrieval",
        "3. Competitor Pricing & Positioning Matrix",
        "4. Financial Attractiveness & Risk Scoring",
        "5. Evidence Verification & Contradiction Audit",
        "6. Business Decision Report Generation"
    ]

    if llm:
        try:
            res = llm.invoke(prompt)
            if hasattr(res, "content") and res.content.strip():
                lines = [line.strip() for line in res.content.split("\n") if line.strip() and (line[0].isdigit() or line.startswith("-"))]
                if lines:
                    plan_steps = lines[:6]
        except Exception as e:
            print(f"[Supervisor] LLM call error: {e}")

    log_summary = f"Planned {len(plan_steps)} sub-tasks for business inquiry decomposition."
    log_agent_activity(query_id, "Supervisor Agent", "COMPLETED", log_summary)

    new_logs = list(state.get("activity_logs", []))
    new_logs.append({
        "agent": "Supervisor Agent",
        "status": "✓ Completed",
        "detail": log_summary
    })

    return {
        **state,
        "current_step": "Supervisor Plan Ready",
        "plan_steps": plan_steps,
        "activity_logs": new_logs
    }
