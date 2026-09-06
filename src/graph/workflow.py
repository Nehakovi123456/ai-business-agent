from langgraph.graph import StateGraph, START, END
from src.graph.state import AgentState
from src.agents.supervisor import supervisor_agent
from src.agents.research_agent import research_agent
from src.agents.rag_agent import rag_agent
from src.agents.competitor_agent import competitor_agent
from src.agents.analysis_agent import analysis_agent
from src.agents.fact_check_agent import fact_check_agent
from src.agents.report_agent import report_agent

def build_business_agent_graph():
    """
    Builds and compiles the 6-agent LangGraph workflow graph.
    """
    workflow = StateGraph(AgentState)

    # Add agent nodes
    workflow.add_node("supervisor", supervisor_agent)
    workflow.add_node("research", research_agent)
    workflow.add_node("rag", rag_agent)
    workflow.add_node("competitor", competitor_agent)
    workflow.add_node("analysis", analysis_agent)
    workflow.add_node("fact_checker", fact_check_agent)
    workflow.add_node("report", report_agent)

    # Wire execution graph
    workflow.add_edge(START, "supervisor")
    
    # Supervisor delegates to specialists
    workflow.add_edge("supervisor", "research")
    workflow.add_edge("research", "rag")
    workflow.add_edge("rag", "competitor")
    
    # Specialists feed findings into Analysis Agent
    workflow.add_edge("competitor", "analysis")
    
    # Analysis passes to Fact Checker
    workflow.add_edge("analysis", "fact_checker")
    
    # Fact Checker passes to Report Agent
    workflow.add_edge("fact_checker", "report")
    
    # Report Agent finishes workflow
    workflow.add_edge("report", END)

    app = workflow.compile()
    return app

def run_agent_workflow(query_text: str, query_id: int = 0, llm_provider: str = "gemini") -> AgentState:
    """
    Executes the full agent workflow for a business inquiry.
    """
    graph = build_business_agent_graph()
    
    initial_state: AgentState = {
        "query_id": query_id,
        "query_text": query_text,
        "llm_provider": llm_provider,
        "current_step": "Initialized",
        "activity_logs": [],
        "plan_steps": [],
        "research_data": [],
        "rag_data": [],
        "competitor_matrix": [],
        "analysis_metrics": {},
        "what_if_scenario": {},
        "fact_check_audit": {},
        "confidence_score": 0.0,
        "report_markdown": "",
        "report_json": {},
        "human_approval_required": False,
        "human_approved": True,
        "human_feedback": ""
    }

    final_state = graph.invoke(initial_state)
    return final_state
