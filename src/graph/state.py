from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    query_id: int
    query_text: str
    llm_provider: str
    current_step: str
    activity_logs: List[Dict[str, Any]]
    
    # Supervisor Plan
    plan_steps: List[str]
    
    # Information gathered by Agents
    research_data: List[Dict[str, Any]]
    rag_data: List[Dict[str, Any]]
    competitor_matrix: List[Dict[str, Any]]
    
    # Feature 2: Risk & Mitigation Assessment
    risk_matrix: List[Dict[str, Any]]
    
    # Decision Analysis, What-If & Feature 3: Scenario Comparison
    analysis_metrics: Dict[str, Any]
    what_if_scenario: Dict[str, Any]
    scenario_comparison: Dict[str, Any]
    
    # Feature 4: "Why This Decision?" Rationale
    why_this_decision: Dict[str, Any]
    
    # Feature 1: Strategic Action Plan Roadmap
    action_plan: Dict[str, Any]
    
    # Fact Verification & Audit
    fact_check_audit: Dict[str, Any]
    confidence_score: float
    
    # Final Output Report
    report_markdown: str
    report_json: Dict[str, Any]
    
    # Human-in-the-Loop Controls
    human_approval_required: bool
    human_approved: Optional[bool]
    human_feedback: Optional[str]
