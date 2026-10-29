from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class GeoLocation(BaseModel):
    city: str
    state: str
    postal_code: str
    country: str = "US"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    service_radius_miles: Optional[float] = 25.0


class ServiceOffering(BaseModel):
    name: str
    category: str
    price_range: str
    turnaround: str
    key_entities: List[str] = Field(default_factory=list)
    wikidata_id: Optional[str] = None


class LocalBusinessProfile(BaseModel):
    business_name: str
    schema_type: str
    phone: str
    address: str
    geo: GeoLocation
    website: str
    services: List[ServiceOffering]
    same_as: List[str] = Field(default_factory=list)
    verified_certifications: List[str] = Field(default_factory=list)
    opening_hours: List[str] = Field(default_factory=lambda: ["Mo-Su 00:00-24:00"])
    area_served: List[str] = Field(default_factory=list)
    knows_about: List[str] = Field(default_factory=list)
    aggregate_rating: Optional[Dict[str, Any]] = None


def extract_entities(profile_data: Dict) -> LocalBusinessProfile:
    services = [
        ServiceOffering(
            name=s.get("name", ""),
            category=s.get("category", "General"),
            price_range=s.get("price_range", "$$"),
            turnaround=s.get("turnaround", "Same Day"),
            key_entities=s.get("key_entities", []),
            wikidata_id=s.get("wikidata_id")
        )
        for s in profile_data.get("services", [])
    ]

    geo_data = profile_data.get("geo", {})
    geo = GeoLocation(
        city=geo_data.get("city", ""),
        state=geo_data.get("state", ""),
        postal_code=geo_data.get("postal_code", ""),
        country=geo_data.get("country", "US"),
        latitude=geo_data.get("latitude"),
        longitude=geo_data.get("longitude"),
        service_radius_miles=geo_data.get("service_radius_miles", 25.0)
    )

    return LocalBusinessProfile(
        business_name=profile_data.get("business_name", ""),
        schema_type=profile_data.get("schema_type", "LocalBusiness"),
        phone=profile_data.get("phone", ""),
        address=profile_data.get("address", ""),
        geo=geo,
        website=profile_data.get("website", ""),
        services=services,
        same_as=profile_data.get("same_as", []),
        verified_certifications=profile_data.get("verified_certifications", []),
        opening_hours=profile_data.get("opening_hours", ["Mo-Su 00:00-24:00"]),
        area_served=profile_data.get("area_served", []),
        knows_about=profile_data.get("knows_about", []),
        aggregate_rating=profile_data.get("aggregate_rating")
    )
