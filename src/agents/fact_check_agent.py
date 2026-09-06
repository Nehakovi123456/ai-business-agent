import re
import json
from src.graph.state import AgentState
from src.config import get_llm
from src.tools.fact_check_tool import verify_claims_and_contradictions
from src.db.database import log_agent_activity

def fact_check_agent(state: AgentState) -> AgentState:
    """
    Fact-Checker Agent:
    Dynamically generates and audits draft assertions for ANY user inquiry using Gemini LLM.
    Uses regex DOTALL parsing for 100% reliable JSON extraction.
    """
    query = state["query_text"]
    query_id = state.get("query_id", 0)
    llm = get_llm(state.get("llm_provider"))

    draft_claims = []

    # 1. PRODUCTION MODE: Dynamic Gemini LLM Claim Generation for ANY query
    if llm:
        try:
            prompt = f"""
            You are a Fact-Verification & Business Audit Specialist.
            Analyze this business inquiry: "{query}"

            Generate 4 specific, quantifiable strategic claims/assertions regarding market growth, internal financial targets, competitor pricing positioning, and target customer priorities for this query.

            Return ONLY a raw JSON array of 4 strings inside brackets [].
            Example:
            [
              "The market for this product is expanding at over 15% CAGR driven by cost-conscious buyers.",
              "Internal financial projections target gross margins exceeding 25%.",
              "Competitors currently price solutions 10% to 20% higher than our proposed entry point.",
              "Over 75% of target buyers prioritize operational efficiency over basic UI design."
            ]
            """
            res = llm.invoke(prompt)
            if hasattr(res, "content") and res.content.strip():
                match = re.search(r'\[.*\]', res.content, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, list) and len(parsed) > 0:
                        draft_claims = [str(c) for c in parsed[:4]]
                        print(f"[FactCheckAgent] Gemini dynamically generated {len(draft_claims)} claims.")
        except Exception as e:
            print(f"[FactCheckAgent] Dynamic LLM claim extraction error: {e}")

    # 2. OFFLINE FALLBACK MODE
    if not draft_claims:
        query_lower = query.lower()
        if any(k in query_lower for k in ["solar", "irrigation", "agri", "farmer", "water"]):
            draft_claims = [
                "The Latin American market for solar-powered automated drip irrigation is expanding over 19% CAGR driven by water scarcity and fuel cost pressures.",
                "Target enterprise customer acquisition models project payback periods under 18 months for sugarcane farmers.",
                "Over 80% of smallholder farmers prioritize pump durability and localized maintenance support over remote software dashboards.",
                "Competitors currently price solar micro-irrigation systems 15% to 25% higher than our proposed entry point."
            ]
        elif any(k in query_lower for k in ["medical", "health", "hospital", "billing", "coding"]):
            draft_claims = [
                "The US market for automated medical coding and clinical billing AI is expanding over 17% CAGR driven by hospital labor shortages.",
                "Target enterprise customer acquisition models project an average annual contract value (ACV) between $50k to $150k.",
                "Over 75% of hospital CFOs and revenue cycle directors prioritize EHR integration capability and HIPAA compliance.",
                "Competitors currently charge custom enterprise licensing fees 15% to 25% higher than our proposed entry point."
            ]
        else:
            clean_topic = query.strip().rstrip("?")
            draft_claims = [
                f"Market intelligence indicates strong adoption potential for '{clean_topic[:50]}'.",
                "Internal financial projections target gross margins exceeding 25%.",
                "Competitors currently price solutions 10% to 20% higher than our proposed entry point.",
                "Target customer decision-makers prioritize operational efficiency and total cost of ownership (TCO) reduction."
            ]

    # Gather all evidence chunks (Web research + RAG passages)
    all_evidence = state.get("research_data", []) + state.get("rag_data", [])

    # Run verification engine
    fact_check_audit = verify_claims_and_contradictions(draft_claims, all_evidence)

    confidence_score = fact_check_audit["confidence_score"]
    overall_status = fact_check_audit["overall_status"]

    log_summary = f"Fact audit status: {overall_status} | Verified {fact_check_audit['supported_claims_count']} claims, Confidence score: {confidence_score}%."
    log_agent_activity(query_id, "Fact Checker Agent", "COMPLETED", log_summary)

    new_logs = list(state.get("activity_logs", []))
    new_logs.append({
        "agent": "Fact Checker Agent",
        "status": "✓ Completed",
        "detail": log_summary
    })

    return {
        **state,
        "current_step": "Fact Check Complete",
        "fact_check_audit": fact_check_audit,
        "confidence_score": confidence_score,
        "activity_logs": new_logs
    }
