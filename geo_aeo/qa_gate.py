import json
import re
from typing import List, Dict, Any
from pydantic import BaseModel, Field


BANNED_FLUFF_PHRASES = [
    "in today's fast-paced world",
    "delve into",
    "testament to",
    "game changer",
    "vibrant tapestry",
    "it is worth noting",
    "beacon of excellence",
    "unlocking the power",
    "revolutionary approach",
    "landscape of"
]


class QAResult(BaseModel):
    passed: bool
    score: int
    findings: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


def extract_schema_from_input(schema_input: str) -> Dict[str, Any]:
    schema_clean = schema_input.strip()
    if "<script" in schema_clean:
        match = re.search(r'<script[^>]*type=[\'"]application/ld\+json[\'"][^>]*>(.*?)</script>', schema_clean, re.DOTALL)
        if match:
            schema_clean = match.group(1).strip()
    return json.loads(schema_clean)


def check_phone_presence(expected_phone: str, content: str) -> bool:
    digits = re.sub(r"[^0-9]", "", expected_phone)
    if not digits:
        return True
    national_10 = digits[-10:] if len(digits) >= 10 else digits
    if national_10 in content:
        return True
    pattern = rf"\(?{national_10[:3]}\)?[-.\s]?{national_10[3:6]}[-.\s]?{national_10[6:]}"
    return bool(re.search(pattern, content))


def validate_aeo_readiness(
    content: str,
    schema_json: str,
    expected_name: str,
    expected_phone: str,
    expected_city: str
) -> QAResult:
    findings = []
    score = 100

    try:
        parsed_schema = extract_schema_from_input(schema_json)
        if parsed_schema.get("@context") != "https://schema.org":
            findings.append("Schema error: @context must be https://schema.org")
            score -= 15
        if not parsed_schema.get("@type"):
            findings.append("Schema error: Missing @type declaration")
            score -= 15
        if not parsed_schema.get("name"):
            findings.append("Schema error: Missing business name in schema")
            score -= 10
        if not parsed_schema.get("address"):
            findings.append("Schema error: Missing PostalAddress in schema")
            score -= 10
    except Exception as exc:
        findings.append(f"Schema syntax failure: {str(exc)}")
        score -= 40

    lower_content = content.lower()
    detected_fluff = [
        phrase for phrase in BANNED_FLUFF_PHRASES
        if phrase in lower_content
    ]
    if detected_fluff:
        findings.append(f"Detected AI filler phrases: {', '.join(detected_fluff)}")
        score -= min(30, len(detected_fluff) * 10)

    if expected_name.lower() not in lower_content:
        findings.append(f"NAP Inconsistency: Business name '{expected_name}' not found in body")
        score -= 15

    if not check_phone_presence(expected_phone, content):
        findings.append(f"NAP Inconsistency: Phone number '{expected_phone}' missing or mismatched")
        score -= 15

    if expected_city.lower() not in lower_content:
        findings.append(f"GEO Inconsistency: Target city '{expected_city}' missing in content")
        score -= 10

    has_table = ("|" in content and "---" in content) or ("<table" in lower_content)
    if not has_table:
        findings.append("AEO Penalty: Missing structured comparison table for entity extraction")
        score -= 15

    has_direct_answer = bool(re.search(r"(>\s*\*\*direct answer:\*\*|data-aeo-chunk|class=[\"']capsule[\"'])", content, re.IGNORECASE))
    if not has_direct_answer:
        findings.append("AEO Penalty: Missing high-density direct answer capsule")
        score -= 15

    score = max(0, min(100, score))
    passed = score >= 80

    return QAResult(
        passed=passed,
        score=score,
        findings=findings,
        metrics={
            "fluff_count": len(detected_fluff),
            "has_table": has_table,
            "has_direct_answer": has_direct_answer,
            "schema_verified": len([f for f in findings if "Schema" in f]) == 0
        }
    )
