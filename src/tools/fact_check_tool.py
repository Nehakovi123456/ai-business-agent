import re
from typing import List, Dict, Any

def verify_claims_and_contradictions(
    draft_claims: List[str],
    evidence_snippets: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Cross-references draft business report claims against gathered evidence snippets.
    Performs keyword matching, numerical verification, and contradiction detection.
    """
    verification_results = []
    supported_count = 0
    unsupported_count = 0
    conflicting_count = 0

    # Combine all evidence content text
    all_evidence_text = " ".join([e.get("content", "") or e.get("snippet", "") for e in evidence_snippets]).lower()
    
    # Extract numbers from evidence snippets for conflict detection
    numbers_in_evidence = re.findall(r'\b\d+(?:\.\d+)?%?\b', all_evidence_text)

    for claim in draft_claims:
        claim_lower = claim.lower()
        
        # Check for matching evidence sources
        matching_sources = []
        for ev in evidence_snippets:
            text = (ev.get("content") or ev.get("snippet") or "").lower()
            # Find matching key phrases or words
            words = [w for w in re.findall(r'\b\w{4,}\b', claim_lower) if w not in ["should", "launch", "would", "about", "their", "market"]]
            matches = sum(1 for w in words if w in text)
            if len(words) > 0 and (matches / len(words)) >= 0.3:
                source_label = ev.get("filename") or ev.get("source") or "Web Search"
                matching_sources.append(source_label)

        # Numerical conflict heuristic
        numbers_in_claim = re.findall(r'\b\d+(?:\.\d+)?%?\b', claim)
        has_conflict = False
        if len(numbers_in_claim) > 0 and len(numbers_in_evidence) > 1:
            # If claim mentions a percentage/number that differs significantly from another source
            for num in numbers_in_claim:
                if "%" in num and any("%" in ev_num and ev_num != num for ev_num in numbers_in_evidence):
                    has_conflict = True

        if has_conflict:
            status = "⚡ Conflicting Evidence"
            conflicting_count += 1
            reason = "Multiple sources report divergent numbers or growth metrics."
        elif len(matching_sources) > 0:
            status = "✓ Supported"
            supported_count += 1
            reason = f"Verified by source: {', '.join(set(matching_sources))}"
        else:
            status = "⚠ Unsupported"
            unsupported_count += 1
            reason = "No direct evidence chunk found in retrieved internal/external sources."

        verification_results.append({
            "claim": claim,
            "status": status,
            "reason": reason,
            "sources": list(set(matching_sources)) if matching_sources else ["N/A"]
        })

    total = len(draft_claims)
    confidence_score = round((supported_count / total * 100.0) if total > 0 else 85.0, 1)

    overall_status = "PASSED" if unsupported_count == 0 and conflicting_count == 0 else "WARNINGS_FOUND"

    return {
        "overall_status": overall_status,
        "confidence_score": confidence_score,
        "supported_claims_count": supported_count,
        "unsupported_claims_count": unsupported_count,
        "conflicting_claims_count": conflicting_count,
        "audit_table": verification_results
    }
