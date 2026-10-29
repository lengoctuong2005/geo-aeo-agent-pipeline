import json
from pathlib import Path
from geo_aeo.entity_miner import extract_entities
from geo_aeo.aeo_synthesizer import generate_authority_page
from geo_aeo.qa_gate import validate_aeo_readiness
from geo_aeo.citation_tracker import audit_citation_readiness, generate_citation_patch


def run():
    example_path = Path("examples/sample_local_business.json")
    with open(example_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    print("=== Step 1: Ingesting Local Entity & NAP Profile ===")
    profile = extract_entities(raw_data)
    print(f"Business: {profile.business_name}")
    print(f"Location: {profile.geo.city}, {profile.geo.state}")
    print(f"Services: {len(profile.services)} offerings mapped")

    print("\n=== Step 2: Generating AEO Authority Artifacts ===")
    artifacts = generate_authority_page(profile)
    out_dir = Path("dist")
    out_dir.mkdir(exist_ok=True)

    (out_dir / "authority_page.md").write_text(artifacts["markdown"], encoding="utf-8")
    (out_dir / "authority_page.html").write_text(artifacts["html"], encoding="utf-8")
    (out_dir / "schema.json").write_text(artifacts["schema_json"], encoding="utf-8")
    print(f"Artifacts rendered to {out_dir}/ (Markdown, HTML5, JSON-LD Schema)")

    print("\n=== Step 3: Executing QA Readiness & Anti-Fluff Gate ===")
    qa = validate_aeo_readiness(
        content=artifacts["markdown"],
        schema_json=artifacts["schema_json"],
        expected_name=profile.business_name,
        expected_phone=profile.phone,
        expected_city=profile.geo.city
    )
    print(f"Readiness Score: {qa.score}/100")
    print(f"Gate Status: {'PASSED' if qa.passed else 'FAILED'}")
    print(f"Metrics: {qa.metrics}")

    print("\n=== Step 4: Tracking AI Citation Potential (Perplexity / SearchGPT) ===")
    test_queries = [
        "emergency root canal in austin tx",
        "cheap pediatric braces in round rock"
    ]

    for q in test_queries:
        audit = audit_citation_readiness(
            content=artifacts["markdown"],
            target_query=q,
            required_entities=["Austin", "Root Canal"] if "root canal" in q else ["Round Rock", "Pediatric"]
        )
        print(f"\nQuery: '{audit.query}'")
        print(f"Citation Probability Score: {audit.citation_score}/100")
        print(f"Status: {'CITABLE' if audit.is_cited else 'UNCITED / GAP DETECTED'}")
        if not audit.is_cited:
            print("Actionable Fixes Required:")
            for fix in audit.actionable_fixes:
                print(f"  - {fix}")
            print("\nGenerating Automated Citation Patch:")
            patch = generate_citation_patch(
                business_name=profile.business_name,
                target_query=q,
                missing_entities=audit.missing_entities,
                city="Round Rock",
                state="TX",
                price_info="$3,200"
            )
            print(patch)


if __name__ == "__main__":
    run()
