import React, { useState, useEffect, useRef } from 'react';
import { X, MapPin, Star, Phone, Navigation } from 'lucide-react';

const MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

interface Clinic {
  place_id: string;
  name: string;
  vicinity: string;
  rating?: number;
  user_ratings_total?: number;
  opening_hours?: { open_now: boolean };
  geometry: { location: { lat: number; lng: number } };
}

interface Props {
  onClose: () => void;
}

export default function NearbyClinicsModal({ onClose }: Props) {
  const [clinics, setClinics] = useState<Clinic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null);
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<google.maps.Map | null>(null);

  useEffect(() => {
    if (!navigator.geolocation) {
      setError('Geolocation not supported.');
      setLoading(false);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const loc = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        setUserLocation(loc);
        fetchClinics(loc);
      },
      () => {
        setError('Could not get your location. Please allow location access.');
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }, []);

  const fetchClinics = async (loc: { lat: number; lng: number }) => {
    if (!MAPS_API_KEY) {
      setError('Google Maps API key not configured. Add VITE_GOOGLE_MAPS_API_KEY to your .env file.');
      setLoading(false);
      return;
    }
    try {
      // Load Maps JS SDK dynamically
      await loadMapsScript();
      const service = new google.maps.places.PlacesService(document.createElement('div'));
      service.nearbySearch(
        {
          location: new google.maps.LatLng(loc.lat, loc.lng),
          radius: 30000,
          type: 'hospital',
          keyword: 'clinic hospital health',
        },
        (results, status) => {
          if (status === google.maps.places.PlacesServiceStatus.OK && results) {
            setClinics(results as Clinic[]);
            initMap(loc, results as Clinic[]);
          } else {
            setError('No clinics found nearby.');
          }
          setLoading(false);
        }
      );
    } catch (e: any) {
      setError(e.message || 'Failed to load map.');
      setLoading(false);
    }
  };

  const loadMapsScript = (): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (window.google?.maps) { resolve(); return; }
      const existing = document.getElementById('gmaps-script');
      if (existing) { existing.addEventListener('load', () => resolve()); return; }
      const script = document.createElement('script');
      script.id = 'gmaps-script';
      script.src = `https://maps.googleapis.com/maps/api/js?key=${MAPS_API_KEY}&libraries=places`;
      script.async = true;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Failed to load Google Maps script.'));
      document.head.appendChild(script);
    });
  };

  const initMap = (center: { lat: number; lng: number }, places: Clinic[]) => {
    if (!mapRef.current) return;
    const map = new google.maps.Map(mapRef.current, {
      center,
      zoom: 14,
      disableDefaultUI: true,
      zoomControl: true,
      styles: [{ featureType: 'poi', stylers: [{ visibility: 'off' }] }],
    });
    mapInstance.current = map;

    // User marker
    new google.maps.Marker({
      position: center,
      map,
      icon: { path: google.maps.SymbolPath.CIRCLE, scale: 8, fillColor: '#26C6BF', fillOpacity: 1, strokeColor: '#fff', strokeWeight: 2 },
      title: 'You are here',
    });

    // Clinic markers
    places.slice(0, 10).forEach((clinic) => {
      const marker = new google.maps.Marker({
        position: clinic.geometry.location,
        map,
        icon: { url: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png' },
        title: clinic.name,
      });
      const info = new google.maps.InfoWindow({
        content: `<div style="font-size:13px;font-weight:700;color:#1A3A38">${clinic.name}</div><div style="font-size:11px;color:#666">${clinic.vicinity}</div>`,
      });
      marker.addListener('click', () => info.open(map, marker));
    });
  };

  const openDirections = (clinic: Clinic) => {
    const { lat, lng } = clinic.geometry.location;
    window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&destination_place_id=${clinic.place_id}`, '_blank');
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-white">
      {/* Header */}
      <div className="bg-[#26C6BF] pt-12 pb-4 px-5 flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-white font-extrabold text-[20px]">Nearby Clinics</h2>
          <p className="text-[#C8F0EC] text-[12px] mt-0.5">Within 30 km of your location</p>
        </div>
        <button onClick={onClose} className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center">
          <X size={18} className="text-white" />
        </button>
      </div>

      {/* Map */}
      <div ref={mapRef} className="w-full h-[220px] shrink-0 bg-[#E8F9F7]">
        {loading && (
          <div className="w-full h-full flex items-center justify-center">
            <div className="w-8 h-8 border-4 border-[#26C6BF] border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-[12px] p-4 text-red-600 text-[13px]">{error}</div>
        )}
        {!loading && !error && clinics.length === 0 && (
          <p className="text-center text-[#7ECCC7] text-sm py-8">No clinics found nearby.</p>
        )}
        {clinics.slice(0, 10).map((clinic) => (
          <div key={clinic.place_id} className="bg-white border border-[#E8F1F1] rounded-[16px] p-4 flex items-start justify-between gap-3 shadow-sm">
            <div className="flex gap-3 flex-1 min-w-0">
              <div className="w-9 h-9 rounded-full bg-[#F2FDFB] border border-[#C8F0EC] flex items-center justify-center shrink-0">
                <MapPin size={16} className="text-[#26C6BF]" />
              </div>
              <div className="min-w-0">
                <p className="font-extrabold text-[14px] text-[#1A3A38] truncate">{clinic.name}</p>
                <p className="text-[#7ECCC7] text-[11px] mt-0.5 truncate">{clinic.vicinity}</p>
                <div className="flex items-center gap-2 mt-1">
                  {clinic.rating && (
                    <div className="flex items-center gap-1">
                      <Star size={10} className="text-[#FFD700] fill-[#FFD700]" />
                      <span className="text-[11px] font-bold text-[#1A3A38]">{clinic.rating}</span>
                      {clinic.user_ratings_total && (
                        <span className="text-[10px] text-[#7ECCC7]">({clinic.user_ratings_total})</span>
                      )}
                    </div>
                  )}
                  {clinic.opening_hours && (
                    <span className={`text-[10px] font-bold ${clinic.opening_hours.open_now ? 'text-green-500' : 'text-red-400'}`}>
                      {clinic.opening_hours.open_now ? 'Open now' : 'Closed'}
                    </span>
                  )}
                </div>
              </div>
            </div>
            <button
              onClick={() => openDirections(clinic)}
              className="shrink-0 w-9 h-9 rounded-full bg-[#26C6BF] flex items-center justify-center shadow-sm"
            >
              <Navigation size={15} className="text-white" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
