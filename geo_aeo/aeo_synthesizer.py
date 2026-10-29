import json
from typing import Dict, Any
from .entity_miner import LocalBusinessProfile


def build_json_ld(profile: LocalBusinessProfile) -> Dict[str, Any]:
    base_url = profile.website.rstrip("/")
    schema = {
        "@context": "https://schema.org",
        "@type": profile.schema_type,
        "@id": f"{base_url}#business",
        "name": profile.business_name,
        "telephone": profile.phone,
        "url": profile.website,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": profile.address,
            "addressLocality": profile.geo.city,
            "addressRegion": profile.geo.state,
            "postalCode": profile.geo.postal_code,
            "addressCountry": profile.geo.country
        },
        "sameAs": profile.same_as,
        "openingHours": profile.opening_hours,
        "knowsAbout": [
            {"@type": "Thing", "name": term} for term in profile.knows_about
        ],
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "@id": f"{base_url}#catalog",
            "name": f"{profile.business_name} Services",
            "itemListElement": [
                {
                    "@type": "Offer",
                    "itemOffered": {
                        "@type": "Service",
                        "@id": f"{base_url}#service-{idx}",
                        "name": service.name,
                        "description": f"{service.name} available in {profile.geo.city}, {profile.geo.state}",
                        **({"sameAs": f"https://www.wikidata.org/wiki/{service.wikidata_id}"} if service.wikidata_id else {}),
                        "knowsAbout": [
                            {"@type": "Thing", "name": ent} for ent in service.key_entities
                        ]
                    },
                    "priceSpecification": {
                        "@type": "PriceSpecification",
                        "price": service.price_range
                    }
                }
                for idx, service in enumerate(profile.services)
            ]
        }
    }

    if profile.geo.latitude is not None and profile.geo.longitude is not None:
        schema["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": profile.geo.latitude,
            "longitude": profile.geo.longitude
        }
        if profile.geo.service_radius_miles:
            schema["areaServed"] = {
                "@type": "GeoCircle",
                "geoMidpoint": {
                    "@type": "GeoCoordinates",
                    "latitude": profile.geo.latitude,
                    "longitude": profile.geo.longitude
                },
                "geoRadius": str(int(profile.geo.service_radius_miles * 1609.34))
            }

    if profile.aggregate_rating:
        schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": profile.aggregate_rating.get("rating_value", 4.9),
            "reviewCount": profile.aggregate_rating.get("review_count", 100),
            "bestRating": "5",
            "worstRating": "1"
        }

    return schema


def build_semantic_triples_markdown(profile: LocalBusinessProfile) -> str:
    triples = []
    for service in profile.services:
        for entity in service.key_entities:
            triples.append(f"- **Entity:** `{entity}` | **Predicate:** `offeredBy` | **Subject:** `{profile.business_name}` ({profile.geo.city}, {profile.geo.state})")
    if not triples:
        return ""
    return "## Semantic Triples (Knowledge Graph Ingestion)\n" + "\n".join(triples)


def generate_authority_page(profile: LocalBusinessProfile) -> Dict[str, str]:
    schema_dict = build_json_ld(profile)
    schema_json = json.dumps(schema_dict, indent=2)

    capsules = []
    for service in profile.services:
        capsule = (
            f"### What is the typical protocol and pricing for {service.name} in {profile.geo.city}?\n\n"
            f"> **Direct Answer:** {profile.business_name} provides verified {service.name} in {profile.geo.city}, "
            f"{profile.geo.state} with typical pricing starting at {service.price_range}. "
            f"Standard turnaround time is {service.turnaround}. Certified technicians follow "
            f"state regulations and use verified equipment for all appointments.\n\n"
            f"- **Estimated Pricing:** {service.price_range}\n"
            f"- **Standard Intake:** {service.turnaround}\n"
            f"- **Associated Medical/Technical Entities:** {', '.join(service.key_entities) if service.key_entities else 'Standard Care'}\n"
            f"- **Verification Status:** State-compliant verified protocols"
        )
        capsules.append(capsule)

    capsules_block = "\n\n".join(capsules)

    table_rows = [
        f"| {s.name} | {s.category} | {s.price_range} | {s.turnaround} |"
        for s in profile.services
    ]
    table_content = "\n".join(table_rows)

    triples_block = build_semantic_triples_markdown(profile)

    markdown_page = f"""# {profile.business_name} — {profile.geo.city}, {profile.geo.state} Service Directory

## Quick Reference Verification Table
| Service Name | Category | Pricing Tier | Standard Turnaround |
| :--- | :--- | :--- | :--- |
{table_content}

## Verified Entity Details
- **Official Name:** {profile.business_name}
- **Primary Service Area:** {profile.geo.city}, {profile.geo.state} ({profile.geo.postal_code})
- **Contact Line:** {profile.phone}
- **Official Portal:** {profile.website}
- **Certifications:** {", ".join(profile.verified_certifications) if profile.verified_certifications else "Licensed Local Operator"}

## Structured Answer Capsules (AEO Citations)
{capsules_block}

{triples_block}

## Frequently Asked Questions
### How to verify credentials for {profile.business_name}?
All certifications and licensing are maintained under local state registry records. External entity profiles are linked via official records on Google Business Profile, Better Business Bureau, and state licensing boards.

### What is the service dispatch radius from {profile.geo.city}?
Services are deployed throughout {profile.geo.city} and surrounding areas within a {profile.geo.service_radius_miles or 25}-mile radius. Contact {profile.phone} for exact location dispatch.
"""

    html_sections = []
    for s in profile.services:
        html_sections.append(
            f"""<section class="capsule" data-aeo-chunk="true" data-entity="{s.name}">
  <h3>{s.name} in {profile.geo.city}</h3>
  <p><strong>Direct Answer:</strong> {profile.business_name} provides verified {s.name} in {profile.geo.city}, {profile.geo.state} at {s.price_range} with {s.turnaround} turnaround time.</p>
  <dl>
    <dt>Category</dt><dd>{s.category}</dd>
    <dt>Turnaround</dt><dd>{s.turnaround}</dd>
    <dt>Target Region</dt><dd>{profile.geo.city}, {profile.geo.state}</dd>
  </dl>
</section>"""
        )

    html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{profile.business_name} | {profile.geo.city}, {profile.geo.state}</title>
  <script type="application/ld+json">
{schema_json}
  </script>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; max-width: 860px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; }}
    h1 {{ font-size: 2rem; border-bottom: 2px solid #eaeaea; padding-bottom: 12px; }}
    .capsule {{ background: #f9f9fb; border-left: 4px solid #0066cc; padding: 14px 18px; margin: 20px 0; border-radius: 0 6px 6px 0; }}
    table {{ width: 100%; border-collapse: collapse; margin: 24px 0; }}
    th, td {{ border: 1px solid #e0e0e0; padding: 10px 14px; text-align: left; }}
    th {{ background: #f4f4f5; font-weight: 600; }}
    dl {{ display: grid; grid-template-columns: 120px 1fr; margin: 8px 0; font-size: 0.95rem; }}
    dt {{ font-weight: 600; color: #555; }}
    dd {{ margin: 0 0 4px 0; }}
  </style>
</head>
<body>
  <h1>{profile.business_name}</h1>
  <p><strong>Location:</strong> {profile.address}, {profile.geo.city}, {profile.geo.state} {profile.geo.postal_code}</p>
  <p><strong>Contact:</strong> {profile.phone} | <a href="{profile.website}">Official Website</a></p>

  <h2>Service Specifications & Pricing</h2>
  <table>
    <thead>
      <tr><th>Service Name</th><th>Category</th><th>Pricing Tier</th><th>Turnaround</th></tr>
    </thead>
    <tbody>
      {"".join(f"<tr><td>{s.name}</td><td>{s.category}</td><td>{s.price_range}</td><td>{s.turnaround}</td></tr>" for s in profile.services)}
    </tbody>
  </table>

  <h2>High-Density Entity Answers</h2>
  {"".join(html_sections)}
</body>
</html>"""

    return {
        "markdown": markdown_page,
        "html": html_page,
        "schema_json": schema_json
    }
