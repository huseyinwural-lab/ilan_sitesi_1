from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()

class GeoLocationResponse(BaseModel):
    city: str
    state: str
    lat: float
    lon: float

@router.get("/validate-zip", response_model=GeoLocationResponse)
async def validate_zip(
    zip_code: str = Query(..., min_length=3),
    country: str = Query(..., min_length=2, max_length=2)
):
    """
    Mock Geocoding Service.
    In prod, connect to Google Maps / Mapbox / OpenStreetMap API.
    """
    country = country.upper()
    
    # Mock Data for testing
    mock_db = {
        "DE": {"10115": {"city": "Berlin", "state": "Berlin", "lat": 52.5200, "lon": 13.4050}},
        "TR": {"34000": {"city": "Istanbul", "state": "Istanbul", "lat": 41.0082, "lon": 28.9784}}
    }
    
    if country in mock_db and zip_code in mock_db[country]:
        return mock_db[country][zip_code]
        
    # Fallback / Default for unknown ZIPS in dev
    return {
        "city": "Unknown City",
        "state": "Unknown State",
        "lat": 0.0,
        "lon": 0.0
    }
