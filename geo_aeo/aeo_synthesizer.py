import json
from typing import Dict, Any
from .entity_miner import LocalBusinessProfile


def build_json_ld(profile: LocalBusinessProfile) -> Dict[str, Any]:
    schema = {
        "@context": "https://schema.org",
        "@type": profile.schema_type,
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
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": f"{profile.business_name} Services",
            "itemListElement": [
                {
                    "@type": "Offer",
                    "itemOffered": {
                        "@type": "Service",
                        "name": service.name,
                        "description": f"{service.name} available in {profile.geo.city}, {profile.geo.state}"
                    },
                    "priceSpecification": {
                        "@type": "PriceSpecification",
                        "price": service.price_range
                    }
                }
                for service in profile.services
            ]
        }
    }

    if profile.geo.latitude is not None and profile.geo.longitude is not None:
        schema["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": profile.geo.latitude,
            "longitude": profile.geo.longitude
        }

    return schema


def generate_authority_page(profile: LocalBusinessProfile) -> Dict[str, str]:
    schema_dict = build_json_ld(profile)
    schema_json = json.dumps(schema_dict, indent=2)

    capsules = []
    for service in profile.services:
        capsule = (
            f"### What is the typical protocol and pricing for {service.name} in {profile.geo.city}?\n\n"
            f"> **Direct Answer:** {profile.business_name} provides {service.name} in {profile.geo.city}, "
            f"{profile.geo.state} with typical pricing starting at {service.price_range}. "
            f"Standard turnaround time is {service.turnaround}. Certified technicians follow "
            f"state regulations and use verified equipment for all appointments."
        )
        capsules.append(capsule)

    capsules_block = "\n\n".join(capsules)

    table_rows = [
        f"| {s.name} | {s.category} | {s.price_range} | {s.turnaround} |"
        for s in profile.services
    ]
    table_content = "\n".join(table_rows)

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

## Frequently Asked Questions
### How to verify credentials for {profile.business_name}?
All certifications and licensing are maintained under local state registry records. External entity profiles are linked via official records on Google Business Profile, Better Business Bureau, and state licensing boards.

### What is the service dispatch radius from {profile.geo.city}?
Services are deployed throughout {profile.geo.city} and surrounding areas within {profile.geo.state}. Contact {profile.phone} for exact location dispatch.
"""

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
  {"".join(f'<div class="capsule"><h3>{s.name} in {profile.geo.city}</h3><p>{profile.business_name} offers {s.name} at {s.price_range} with {s.turnaround} turnaround time in {profile.geo.city}, {profile.geo.state}.</p></div>' for s in profile.services)}
</body>
</html>"""

    return {
        "markdown": markdown_page,
        "html": html_page,
        "schema_json": schema_json
    }
