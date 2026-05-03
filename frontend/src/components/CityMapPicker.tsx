import { useState, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from 'react-leaflet';
import { clsx } from 'clsx';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import styles from './CityMapPicker.module.css';

interface CityMapPickerProps {
  fromCity: string;
  toCity: string;
  onFromCityChange: (city: string) => void;
  onToCityChange: (city: string) => void;
}

const DEFAULT_CENTER: [number, number] = [53.9045, 27.5615];
const DEFAULT_ZOOM = 7;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
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
}

function CityMarker({ position }: CityMarkerProps) {
  const map = useMap();

  if (position) {
    map.flyTo(position, 10);
  }

  return position ? <Marker position={position} opacity={0.85} /> : null;
}

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
    const address = data.address;
    const city = address.city || address.town || address.village || address.municipality || address.county;

    if (city) {
      return city;
    }

    return data.display_name?.split(',')[0] || 'Unknown location';
  } catch (error) {
    console.error('Reverse geocoding error:', error);
    return `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
  }
}

const MAJOR_CITIES: { name: string; lat: number; lng: number }[] = [
  { name: 'Минск', lat: 53.9045, lng: 27.5615 },
  { name: 'Гомель', lat: 52.4419, lng: 30.9918 },
  { name: 'Могилёв', lat: 53.9168, lng: 30.3449 },
  { name: 'Витебск', lat: 55.1993, lng: 30.2046 },
  { name: 'Гродно', lat: 53.6693, lng: 23.8151 },
  { name: 'Брест', lat: 52.0976, lng: 23.6907 },
  { name: 'Бобруйск', lat: 53.1428, lng: 29.2214 },
  { name: 'Барановичи', lat: 52.7346, lng: 26.0165 },
];

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

  const handleMapClick = useCallback(async (lat: number, lng: number) => {
    if (!selectingFor) return;

    setIsLoading(true);
    setError(null);

    try {
      const cityName = await reverseGeocode(lat, lng);

      if (selectingFor === 'from') {
        setFromPosition([lat, lng]);
        onFromCityChange(cityName);
      } else {
        setToPosition([lat, lng]);
        onToCityChange(cityName);
      }
      setSelectingFor(null);
    } catch (err) {
      setError('Не удалось определить город');
    } finally {
      setIsLoading(false);
    }
  }, [selectingFor, onFromCityChange, onToCityChange]);

  const handleCityQuickSelect = useCallback((city: { name: string; lat: number; lng: number }) => {
    setError(null);
    if (!fromCity) {
      setFromPosition([city.lat, city.lng]);
      onFromCityChange(city.name);
    } else if (!toCity) {
      setToPosition([city.lat, city.lng]);
      onToCityChange(city.name);
    } else {
      setFromPosition([city.lat, city.lng]);
      onFromCityChange(city.name);
    }
  }, [fromCity, toCity, onFromCityChange, onToCityChange]);

  const toggleSelectingFor = (target: 'from' | 'to') => {
    setSelectingFor((current) => (current === target ? null : target));
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.actions}>
        <button
          type="button"
          onClick={() => toggleSelectingFor('from')}
          disabled={isLoading}
          className={clsx(styles.actionButton, selectingFor === 'from' && styles.actionButtonActive)}
          aria-pressed={selectingFor === 'from'}
        >
          <span className={styles.dotFrom} />
          {selectingFor === 'from' ? 'Кликните по карте, чтобы выбрать «Откуда»' : 'Указать «Откуда» на карте'}
        </button>
        <button
          type="button"
          onClick={() => toggleSelectingFor('to')}
          disabled={isLoading}
          className={clsx(styles.actionButton, selectingFor === 'to' && styles.actionButtonActive)}
          aria-pressed={selectingFor === 'to'}
        >
          <span className={styles.dotTo} />
          {selectingFor === 'to' ? 'Кликните по карте, чтобы выбрать «Куда»' : 'Указать «Куда» на карте'}
        </button>
      </div>

      <div className={styles.chipsRow}>
        <span className={styles.chipsLabel}>Популярные города:</span>
        {MAJOR_CITIES.map((city) => (
          <button
            key={city.name}
            type="button"
            className={styles.cityChip}
            onClick={() => handleCityQuickSelect(city)}
          >
            {city.name}
          </button>
        ))}
      </div>

      <div className={clsx(styles.mapBox, selectingFor && styles.mapBoxActive)}>
        {selectingFor && (
          <div className={styles.mapBadge}>
            <span className={selectingFor === 'from' ? styles.dotFrom : styles.dotTo} />
            {selectingFor === 'from' ? 'Выберите место отправления' : 'Выберите место прибытия'}
          </div>
        )}

        <MapContainer
          center={DEFAULT_CENTER}
          zoom={DEFAULT_ZOOM}
          style={{ height: '100%', width: '100%' }}
          scrollWheelZoom={true}
          zoomControl={false}
        >
          <TileLayer
            attribution=''
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapClickHandler onMapClick={handleMapClick} />
          {fromPosition && <CityMarker position={fromPosition} />}
          {toPosition && <CityMarker position={toPosition} />}
        </MapContainer>
      </div>

      {error && <div className={styles.error}>{error}</div>}
    </div>
  );
}
