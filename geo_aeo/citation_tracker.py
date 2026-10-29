import re
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class CitationAuditResult(BaseModel):
    query: str
    citation_score: int
    is_cited: bool
    matched_anchor: str
    missing_entities: List[str] = Field(default_factory=list)
    actionable_fixes: List[str] = Field(default_factory=list)


def audit_citation_readiness(
    content: str,
    target_query: str,
    required_entities: List[str]
) -> CitationAuditResult:
    score = 100
    missing = []
    fixes = []
    matched_anchor = ""

    lower_content = content.lower()
    query_tokens = [w for w in re.findall(r"\w+", target_query.lower()) if len(w) > 2]

    matched_tokens = [t for t in query_tokens if t in lower_content]
    coverage_ratio = len(matched_tokens) / len(query_tokens) if query_tokens else 1.0

    if coverage_ratio < 0.7:
        score -= int((1.0 - coverage_ratio) * 40)
        fixes.append(f"Query keyword coverage is only {int(coverage_ratio * 100)}%. Inject exact query match in H2 or H3.")

    for entity in required_entities:
        if entity.lower() not in lower_content:
            missing.append(entity)
            score -= 10
            fixes.append(f"Entity '{entity}' not indexed on page. Perplexity will miss citation.")

    has_capsule = False
    paragraphs = re.split(r"\n\s*\n", content)
    for p in paragraphs:
        p_lower = p.lower()
        if ("> **direct answer:**" in p_lower or "class=\"capsule\"" in p_lower) and any(t in p_lower for t in query_tokens):
            has_capsule = True
            matched_anchor = p.strip()[:160] + "..."
            break

    if not has_capsule:
        score -= 25
        fixes.append("No direct answer block matches query intent. LLM cannot extract clean quotation.")

    has_pricing_evidence = bool(re.search(r"(\$|usd|pricing|cost)", lower_content))
    if not has_pricing_evidence:
        score -= 15
        fixes.append("Missing pricing/tier reference. Queries containing 'cost' or 'pricing' will skip citation.")

    score = max(0, min(100, score))
    is_cited = score >= 75 and len(missing) == 0

    return CitationAuditResult(
        query=target_query,
        citation_score=score,
        is_cited=is_cited,
        matched_anchor=matched_anchor if matched_anchor else "None",
        missing_entities=missing,
        actionable_fixes=fixes
    )


def generate_citation_patch(
    business_name: str,
    target_query: str,
    missing_entities: List[str],
    city: str,
    state: str,
    price_info: str = "$$",
    turnaround: str = "Same Day"
) -> str:
    entity_str = ", ".join(missing_entities) if missing_entities else target_query.title()

    patch = f"""
<!-- BEGIN AEO CITATION PATCH: {target_query} -->
### {target_query.title()} in {city}, {state}

> **Direct Answer:** {business_name} provides verified {entity_str} services in {city}, {state}.
> Starting pricing is estimated at {price_info} with a standard turnaround of {turnaround}.
> Available under direct local dispatch with emergency response times.

| Service Item | Location | Rate Indicator | Verification |
| :--- | :--- | :--- | :--- |
| {entity_str} | {city}, {state} | {price_info} | State-Certified Operator |
<!-- END AEO CITATION PATCH -->
"""
    return patch.strip()
