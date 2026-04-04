import { useState, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface CityMapPickerProps {
  fromCity: string;
  toCity: string;
  onFromCityChange: (city: string) => void;
  onToCityChange: (city: string) => void;
}

// Default center - Belarus
const DEFAULT_CENTER: [number, number] = [53.9045, 27.5615];
const DEFAULT_ZOOM = 7;

// Fix for default marker icon
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

interface MapClickHandlerProps {
  onMapClick: (lat: number, lng: number) => void;
}

function MapClickHandler({ onMapClick }: MapClickHandlerProps) {
  useMapEvents({
    click: (e) => {
      onMapClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

interface CityMarkerProps {
  position: [number, number] | null;
  label: string;
}

function CityMarker({ position, label }: CityMarkerProps) {
  const map = useMap();
  
  if (position) {
    map.flyTo(position, 10);
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const CustomPopup = L.popup({ closeButton: false });

  return position ? (
    <Marker position={position} opacity={0.8}>
    </Marker>
  ) : null;
}

// Reverse geocoding using Nominatim
async function reverseGeocode(lat: number, lng: number): Promise<string> {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=10&addressdetails=1`,
      {
        headers: {
          'User-Agent': 'RoadMate/1.0',
        },
      }
    );
    
    if (!response.ok) {
      throw new Error('Geocoding failed');
    }
    
    const data = await response.json();
    
    // Try to get city name from address
    const address = data.address;
    const city = address.city || address.town || address.village || address.municipality || address.county;
    
    if (city) {
      return city;
    }
    
    // Fallback to display name
    return data.display_name?.split(',')[0] || 'Unknown location';
  } catch (error) {
    console.error('Reverse geocoding error:', error);
    return `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
  }
}

export default function CityMapPicker({
  fromCity,
  toCity,
  onFromCityChange,
  onToCityChange,
}: CityMapPickerProps) {
  const [fromPosition, setFromPosition] = useState<[number, number] | null>(null);
  const [toPosition, setToPosition] = useState<[number, number] | null>(null);
  const [selectingFor, setSelectingFor] = useState<'from' | 'to' | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Predefined major cities in Belarus for quick selection
  const majorCities: { name: string; lat: number; lng: number }[] = [
    { name: 'Минск', lat: 53.9045, lng: 27.5615 },
    { name: 'Гомель', lat: 52.4419, lng: 30.9918 },
    { name: 'Могилёв', lat: 53.9168, lng: 30.3449 },
    { name: 'Витебск', lat: 55.1993, lng: 30.2046 },
    { name: 'Гродно', lat: 53.6693, lng: 23.8151 },
    { name: 'Брест', lat: 52.0976, lng: 23.6907 },
    { name: 'Бобруйск', lat: 53.1428, lng: 29.2214 },
    { name: 'Барановичи', lat: 52.7346, lng: 26.0165 },
  ];

  const handleMapClick = useCallback(async (lat: number, lng: number) => {
    if (!selectingFor) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const cityName = await reverseGeocode(lat, lng);
      
      if (selectingFor === 'from') {
        setFromPosition([lat, lng]);
        onFromCityChange(cityName);
        setSelectingFor(null);
      } else if (selectingFor === 'to') {
        setToPosition([lat, lng]);
        onToCityChange(cityName);
        setSelectingFor(null);
      }
    } catch (err) {
      setError('Не удалось определить город');
    } finally {
      setIsLoading(false);
    }
  }, [selectingFor, onFromCityChange, onToCityChange]);

  const handleCityQuickSelect = useCallback(async (city: { name: string; lat: number; lng: number }, type: 'from' | 'to') => {
    setIsLoading(true);
    setError(null);
    
    try {
      if (type === 'from') {
        setFromPosition([city.lat, city.lng]);
        onFromCityChange(city.name);
        setSelectingFor(null);
      } else {
        setToPosition([city.lat, city.lng]);
        onToCityChange(city.name);
        setSelectingFor(null);
      }
    } catch (err) {
      setError('Не удалось выбрать город');
    } finally {
      setIsLoading(false);
    }
  }, [onFromCityChange, onToCityChange]);

  const handleClearFrom = () => {
    setFromPosition(null);
    onFromCityChange('');
  };

  const handleClearTo = () => {
    setToPosition(null);
    onToCityChange('');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* City Selection Buttons */}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: '200px' }}>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, marginBottom: '6px', color: '#374151' }}>
            Откуда
          </label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              value={fromCity}
              onChange={(e) => onFromCityChange(e.target.value)}
              placeholder="Выберите на карте или введите"
              style={{
                flex: 1,
                padding: '10px 14px',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '0.875rem',
              }}
            />
            {fromPosition && (
              <button
                type="button"
                onClick={handleClearFrom}
                style={{
                  padding: '8px 12px',
                  background: '#fee2e2',
                  border: '1px solid #fecaca',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  color: '#dc2626',
                }}
              >
                ✕
              </button>
            )}
          </div>
          <button
            type="button"
            onClick={() => setSelectingFor('from')}
            disabled={isLoading}
            style={{
              marginTop: '8px',
              padding: '8px 16px',
              background: selectingFor === 'from' ? '#2563eb' : '#eff6ff',
              color: selectingFor === 'from' ? '#white' : '#2563eb',
              border: '1px solid #2563eb',
              borderRadius: '6px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              fontSize: '0.875rem',
              fontWeight: 500,
              opacity: isLoading ? 0.7 : 1,
            }}
          >
            {selectingFor === 'from' ? '点击地图选择位置...' : '📍 Указать на карте'}
          </button>
        </div>

        <div style={{ flex: 1, minWidth: '200px' }}>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, marginBottom: '6px', color: '#374151' }}>
            Куда
          </label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              value={toCity}
              onChange={(e) => onToCityChange(e.target.value)}
              placeholder="Выберите на карте или введите"
              style={{
                flex: 1,
                padding: '10px 14px',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '0.875rem',
              }}
            />
            {toPosition && (
              <button
                type="button"
                onClick={handleClearTo}
                style={{
                  padding: '8px 12px',
                  background: '#fee2e2',
                  border: '1px solid #fecaca',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  color: '#dc2626',
                }}
              >
                ✕
              </button>
            )}
          </div>
          <button
            type="button"
            onClick={() => setSelectingFor('to')}
            disabled={isLoading}
            style={{
              marginTop: '8px',
              padding: '8px 16px',
              background: selectingFor === 'to' ? '#2563eb' : '#eff6ff',
              color: selectingFor === 'to' ? '#white' : '#2563eb',
              border: '1px solid #2563eb',
              borderRadius: '6px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              fontSize: '0.875rem',
              fontWeight: 500,
              opacity: isLoading ? 0.7 : 1,
            }}
          >
            {selectingFor === 'to' ? '点击地图选择位置...' : '📍 Указать на карте'}
          </button>
        </div>
      </div>

      {/* Quick City Selection */}
      {!selectingFor && (
        <div>
          <p style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '8px' }}>
            Или выберите из крупных городов:
          </p>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {majorCities.map((city) => (
              <button
                key={city.name}
                type="button"
                onClick={() => {
                  if (!fromCity) {
                    handleCityQuickSelect(city, 'from');
                  } else if (!toCity) {
                    handleCityQuickSelect(city, 'to');
                  } else {
                    handleCityQuickSelect(city, 'from');
                  }
                }}
                style={{
                  padding: '6px 12px',
                  background: '#f3f4f6',
                  border: '1px solid #e5e7eb',
                  borderRadius: '16px',
                  cursor: 'pointer',
                  fontSize: '0.75rem',
                  color: '#374151',
                }}
              >
                {city.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Map */}
      <div style={{
        height: selectingFor ? '350px' : '250px',
        border: '1px solid #e5e7eb',
        borderRadius: '12px',
        overflow: 'hidden',
        position: 'relative',
      }}>
        {selectingFor && (
          <div style={{
            position: 'absolute',
            top: '10px',
            left: '10px',
            zIndex: 1000,
            background: 'white',
            padding: '8px 12px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            fontSize: '0.875rem',
            fontWeight: 500,
          }}>
            {selectingFor === 'from' ? '��� Выберите место отправления' : '📍 Выберите место прибытия'}
          </div>
        )}
        
        <MapContainer
          center={DEFAULT_CENTER}
          zoom={DEFAULT_ZOOM}
          style={{ height: '100%', width: '100%' }}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapClickHandler onMapClick={handleMapClick} />
          {fromPosition && <CityMarker position={fromPosition} label={fromCity || 'Откуда'} />}
          {toPosition && <CityMarker position={toPosition} label={toCity || 'Куда'} />}
        </MapContainer>
      </div>

      {error && (
        <div style={{ color: '#dc2626', fontSize: '0.875rem' }}>
          {error}
        </div>
      )}
    </div>
  );
}