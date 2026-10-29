# Autonomous GEO & AEO Authority Agent Pipeline

A production-ready pipeline for building, validating, and monitoring AI GEO (Generative Engine Optimization) and AEO (Answer Engine Optimization) authority pages for local businesses.

Built specifically to get local businesses directly cited in answer engines like Perplexity, ChatGPT Search, and Google AI Overviews.

---

## The Problem: Traditional SEO vs. Generative Engine Optimization (GEO/AEO)

Traditional SEO relies on keyword density, backlink quantity, and long-form filler content. Large language models and generative search engines do not read content like Google's 2015 crawler:

1. **Entity Gaps:** LLMs extract semantic triples (Subject, Predicate, Object) tied to Knowledge Graph entities. Loose text without explicit Schema.org structure gets ignored.
2. **Citation Windows:** Perplexity and SearchGPT look for high-density, 40 to 60 word factual answer capsules right below target question headers.
3. **Fluff Penalty:** Unstructured, conversational filler increases token entropy and causes answer extractors to skip the domain.
4. **NAP Drift:** Discrepancies in Name, Address, and Phone numbers break local grounding in AI answers.

This repository automates the end-to-end lifecycle: entity extraction, authority page generation, deterministic QA gates, and automated citation repair.

---

## Architecture Topology

```text
[Local Business Profile / JSON]
           │
           ▼
┌─────────────────────────────────┐
│ 1. Entity & NAP Miner           │  Extracts Knowledge Graph anchors,
│    (geo_aeo/entity_miner.py)    │  services, pricing tiers, and coordinates
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ 2. AEO Authority Synthesizer    │  Generates JSON-LD (LocalBusiness),
│    (geo_aeo/aeo_synthesizer.py) │  direct Answer Capsules, and comparison tables
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ 3. Deterministic QA Gate        │  Validates schema syntax, NAP integrity,
│    (geo_aeo/qa_gate.py)         │  and blocks low-grade AI filler phrases
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ 4. AI Citation Tracker & Fixer  │  Evaluates query citation probability and
│    (geo_aeo/citation_tracker.py)│  auto-generates patches for uncited queries
└─────────────────────────────────┘
```

---

## Quick Start

### Installation

```bash
git clone https://github.com/lengoctuong2005/geo-aeo-agent-pipeline.git
cd geo-aeo-agent-pipeline
pip install -e .
```

### Run Full Pipeline Demo

Execute the end-to-end verification demo on a sample Austin emergency dental practice:

```bash
python3 run_demo.py
```

### Run Automated Tests

```bash
python3 -m pytest tests/ -v
```

---

## CLI Usage

### 1. Generate AEO Authority Site

Generate structured Markdown, HTML5, and valid Schema.org JSON-LD from a business profile:

```bash
geo-aeo generate \
  --input examples/sample_local_business.json \
  --outdir dist/
```

### 2. Run Deterministic QA Gate

Ensure the generated page contains zero AI filler words, has valid Schema markup, and maintains exact NAP consistency:

```bash
geo-aeo qa \
  --file dist/austin_premier_emergency_dental_authority.md \
  --schema dist/austin_premier_emergency_dental_schema.json \
  --name "Austin Premier Emergency Dental" \
  --phone "+1-512-555-0199" \
  --city "Austin"
```

Output:
```text
QA Readiness Score: 100/100
Status: PASSED
```

### 3. Audit AI Citation Readiness

Test whether a page will get cited by Perplexity or ChatGPT Search for a target query:

```bash
geo-aeo audit-citation \
  --file dist/austin_premier_emergency_dental_authority.md \
  --query "emergency root canal in austin tx" \
  --entities "Austin" "Root Canal"
```

### 4. Auto-Generate Citation Fix Patch

When an audit reveals an uncited query or missing entity, automatically generate the exact Answer Capsule and comparison table row to patch the site:

```bash
geo-aeo fix-citation \
  --business "Austin Premier Emergency Dental" \
  --query "cheap pediatric braces in round rock" \
  --city "Round Rock" \
  --state "TX" \
  --entities "Round Rock" "Pediatric Braces"
```

---

## Claude Code CLI Integration

This pipeline is designed to be called directly by autonomous agents running inside Claude Code CLI or custom agent loops:

```bash
claude "Read examples/sample_local_business.json, run geo-aeo generate, audit citation for query 'emergency tooth extraction austin', and patch missing entities."
```

Deterministic verification gates ensure agents cannot publish hallucinated or unformatted copy to client sites.

---

## License

MIT License. Authored by [Le Ngoc Tuong](https://github.com/lengoctuong2005).
