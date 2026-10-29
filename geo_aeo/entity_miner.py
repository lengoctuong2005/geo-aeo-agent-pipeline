from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class GeoLocation(BaseModel):
    city: str
    state: str
    postal_code: str
    country: str = "US"
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ServiceOffering(BaseModel):
    name: str
    category: str
    price_range: str
    turnaround: str
    key_entities: List[str] = Field(default_factory=list)


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


def extract_entities(profile_data: Dict) -> LocalBusinessProfile:
    services = [
        ServiceOffering(
            name=s.get("name", ""),
            category=s.get("category", "General"),
            price_range=s.get("price_range", "$$"),
            turnaround=s.get("turnaround", "Same Day"),
            key_entities=s.get("key_entities", [])
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
        longitude=geo_data.get("longitude")
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
        verified_certifications=profile_data.get("verified_certifications", [])
    )
