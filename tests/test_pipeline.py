import json
import pytest
from geo_aeo.entity_miner import extract_entities, LocalBusinessProfile
from geo_aeo.aeo_synthesizer import generate_authority_page, build_json_ld
from geo_aeo.qa_gate import validate_aeo_readiness
from geo_aeo.citation_tracker import audit_citation_readiness, generate_citation_patch


SAMPLE_RAW_DATA = {
    "business_name": "Austin Premier Emergency Dental",
    "schema_type": "Dentist",
    "phone": "+1-512-555-0199",
    "address": "401 Congress Ave, Suite 1200",
    "geo": {
        "city": "Austin",
        "state": "TX",
        "postal_code": "78701",
        "country": "US",
        "latitude": 30.2672,
        "longitude": -97.7431
    },
    "website": "https://austinemergencydental.example.com",
    "services": [
        {
            "name": "Emergency Root Canal",
            "category": "Endodontics",
            "price_range": "$900 - $1,500",
            "turnaround": "Same Day Immediate",
            "key_entities": ["Pulpitis", "Endodontics"]
        }
    ],
    "same_as": ["https://www.bbb.org/example"],
    "verified_certifications": ["Texas Dental Board"]
}


def test_entity_extraction():
    profile = extract_entities(SAMPLE_RAW_DATA)
    assert profile.business_name == "Austin Premier Emergency Dental"
    assert profile.geo.city == "Austin"
    assert len(profile.services) == 1
    assert profile.services[0].name == "Emergency Root Canal"


def test_schema_and_page_generation():
    profile = extract_entities(SAMPLE_RAW_DATA)
    result = generate_authority_page(profile)

    assert "markdown" in result
    assert "html" in result
    assert "schema_json" in result

    schema = json.loads(result["schema_json"])
    assert schema["@context"] == "https://schema.org"
    assert schema["@type"] == "Dentist"
    assert schema["telephone"] == "+1-512-555-0199"
    assert schema["geo"]["latitude"] == 30.2672


def test_qa_gate_passes_clean_content():
    profile = extract_entities(SAMPLE_RAW_DATA)
    result = generate_authority_page(profile)

    qa = validate_aeo_readiness(
        content=result["markdown"],
        schema_json=result["schema_json"],
        expected_name=profile.business_name,
        expected_phone=profile.phone,
        expected_city=profile.geo.city
    )

    assert qa.passed is True
    assert qa.score >= 80
    assert len(qa.findings) == 0


def test_qa_gate_catches_fluff_and_mismatches():
    fluffy_content = (
        "In today's fast-paced world, delve into our revolutionary approach. "
        "It serves as a testament to our excellence."
    )
    empty_schema = "{}"

    qa = validate_aeo_readiness(
        content=fluffy_content,
        schema_json=empty_schema,
        expected_name="NonExistent Dental",
        expected_phone="1234567890",
        expected_city="Austin"
    )

    assert qa.passed is False
    assert qa.score < 50
    assert any("filler phrases" in f for f in qa.findings)


def test_citation_tracker_and_patching():
    profile = extract_entities(SAMPLE_RAW_DATA)
    result = generate_authority_page(profile)

    audit = audit_citation_readiness(
        content=result["markdown"],
        target_query="emergency root canal in austin",
        required_entities=["Austin", "Root Canal"]
    )

    assert audit.is_cited is True
    assert audit.citation_score >= 75

    poor_content = "We fix teeth. Call us anytime."
    failing_audit = audit_citation_readiness(
        content=poor_content,
        target_query="emergency root canal in austin",
        required_entities=["Root Canal", "Austin"]
    )

    assert failing_audit.is_cited is False
    assert len(failing_audit.actionable_fixes) > 0

    patch = generate_citation_patch(
        business_name="Austin Premier Emergency Dental",
        target_query="emergency root canal in austin",
        missing_entities=["Pulpitis", "Root Canal Therapy"],
        city="Austin",
        state="TX",
        price_info="$900"
    )

    assert "BEGIN AEO CITATION PATCH" in patch
    assert "Austin Premier Emergency Dental" in patch
    assert "$900" in patch
