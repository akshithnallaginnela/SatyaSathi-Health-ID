from fastapi import APIRouter
import os
import requests

router = APIRouter(prefix="/api/clinics", tags=["Clinics Near Me"])

@router.get("/nearest")
async def get_nearest_clinics(lat: float, lng: float):
    """
    Fetches the nearest clinics/hospitals from Google Places API.
    Uses mock data if GOOGLE_MAPS_API_KEY is not defined.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("WARNING: GOOGLE_MAPS_API_KEY missing. Returning mock clinics.")
        return [
            {"name": "City Health Clinic", "distance": "1.2 km", "type": "Dr. Sharma • General Physician"},
            {"name": "HeartCare Center", "distance": "3.5 km", "type": "Dr. Patel • Cardiologist"}
        ]
        
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=5000&type=hospital&key={api_key}"
    resp = requests.get(url)
    
    if resp.ok:
        data = resp.json()
        clinics = []
        for p in data.get("results", [])[:5]:
            clinics.append({
                "name": p.get("name"),
                "distance": "Nearby (Requires Matrix API)",  # Just a placeholder for distance
                "type": p.get("vicinity") or "Healthcare Facility"
            })
        return clinics
        
    return {"error": "Failed to fetch from Google Maps API."}
