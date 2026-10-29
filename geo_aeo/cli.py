import argparse
import json
import sys
from pathlib import Path
from .entity_miner import extract_entities
from .aeo_synthesizer import generate_authority_page
from .qa_gate import validate_aeo_readiness
from .citation_tracker import audit_citation_readiness, generate_citation_patch


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geo-aeo",
        description="Autonomous AEO/GEO Authority Site & AI Citation Pipeline"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser("generate", help="Generate AEO authority site from profile JSON")
    gen_parser.add_argument("--input", "-i", required=True, help="Path to profile JSON")
    gen_parser.add_argument("--outdir", "-o", default="dist", help="Output directory")

    qa_parser = subparsers.add_parser("qa", help="Validate AEO readiness and schema compliance")
    qa_parser.add_argument("--file", "-f", required=True, help="Path to generated markdown or html")
    qa_parser.add_argument("--schema", "-s", required=True, help="Path to JSON-LD schema file")
    qa_parser.add_argument("--name", required=True, help="Expected business name")
    qa_parser.add_argument("--phone", required=True, help="Expected phone number")
    qa_parser.add_argument("--city", required=True, help="Expected target city")

    cite_parser = subparsers.add_parser("audit-citation", help="Audit AI citation potential for specific query")
    cite_parser.add_argument("--file", "-f", required=True, help="Path to target page")
    cite_parser.add_argument("--query", "-q", required=True, help="Target search query")
    cite_parser.add_argument("--entities", "-e", nargs="+", default=[], help="Required entity names")

    patch_parser = subparsers.add_parser("fix-citation", help="Generate citation fix patch for uncited page")
    patch_parser.add_argument("--business", "-b", required=True, help="Business name")
    patch_parser.add_argument("--query", "-q", required=True, help="Failing target query")
    patch_parser.add_argument("--city", required=True, help="Target city")
    patch_parser.add_argument("--state", required=True, help="Target state")
    patch_parser.add_argument("--entities", "-e", nargs="+", default=[], help="Missing entity names")

    return parser


def run_generate(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.exists():
        sys.stderr.write(f"Input file not found: {args.input}\n")
        return 1

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    profile = extract_entities(data)
    result = generate_authority_page(profile)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    slug = profile.business_name.lower().replace(" ", "_")
    md_file = outdir / f"{slug}_authority.md"
    html_file = outdir / f"{slug}_authority.html"
    schema_file = outdir / f"{slug}_schema.json"

    with open(md_file, "w", encoding="utf-8") as f:
        f.write(result["markdown"])
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(result["html"])
    with open(schema_file, "w", encoding="utf-8") as f:
        f.write(result["schema_json"])

    print(f"Generated AEO site successfully:")
    print(f"  - Markdown: {md_file}")
    print(f"  - HTML:     {html_file}")
    print(f"  - Schema:   {schema_file}")
    return 0


def run_qa(args: argparse.Namespace) -> int:
    with open(args.file, "r", encoding="utf-8") as f:
        content = f.read()
    with open(args.schema, "r", encoding="utf-8") as f:
        schema_json = f.read()

    res = validate_aeo_readiness(
        content=content,
        schema_json=schema_json,
        expected_name=args.name,
        expected_phone=args.phone,
        expected_city=args.city
    )

    print(f"QA Readiness Score: {res.score}/100")
    print(f"Status: {'PASSED' if res.passed else 'FAILED'}")
    if res.findings:
        print("Findings:")
        for finding in res.findings:
            print(f"  - {finding}")
    return 0 if res.passed else 1


def run_audit_citation(args: argparse.Namespace) -> int:
    with open(args.file, "r", encoding="utf-8") as f:
        content = f.read()

    res = audit_citation_readiness(
        content=content,
        target_query=args.query,
        required_entities=args.entities
    )

    print(f"Query: '{res.query}'")
    print(f"Citation Score: {res.citation_score}/100")
    print(f"AI Citation Status: {'CITABLE' if res.is_cited else 'AT RISK / UNCITED'}")
    print(f"Matched Anchor: {res.matched_anchor}")
    if res.actionable_fixes:
        print("Actionable Fixes:")
        for fix in res.actionable_fixes:
            print(f"  - {fix}")
    return 0 if res.is_cited else 1


def run_fix_citation(args: argparse.Namespace) -> int:
    patch = generate_citation_patch(
        business_name=args.business,
        target_query=args.query,
        missing_entities=args.entities,
        city=args.city,
        state=args.state
    )
    print("Generated AEO Citation Patch:")
    print(patch)
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "generate": run_generate,
        "qa": run_qa,
        "audit-citation": run_audit_citation,
        "fix-citation": run_fix_citation
    }

    handler = dispatch.get(args.command)
    if handler:
        sys.exit(handler(args))
    sys.exit(1)


if __name__ == "__main__":
    main()
