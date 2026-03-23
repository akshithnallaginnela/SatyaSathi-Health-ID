from typing import List
from fastapi import APIRouter, Depends, Query
import random

router = APIRouter(prefix="/api/clinics", tags=["Clinics"])

@router.get("/nearest")
async def get_nearest_clinics(
    lat: float = Query(...), 
    lng: float = Query(...),
    radius_km: float = Query(5.0)
):
    """Return mock clinics nearby."""
    clinics = [
        {"id": "c1", "name": "Vital Health Clinic", "address": "123 MG Road, Bangalore", "distance": "0.8 km", "type": "GP"},
        {"id": "c2", "name": "MediCare Plus", "address": "45 Indiranagar, Bangalore", "distance": "2.1 km", "type": "Diagnostic Center"},
        {"id": "c3", "name": "City Life Hospital", "address": "Sector 4, HSR Layout", "distance": "3.5 km", "type": "Hospital"},
        {"id": "c4", "name": "Apex Diagonostics", "address": "Richmond Town", "distance": "1.2 km", "type": "Laboratory"},
    ]
    return clinics
