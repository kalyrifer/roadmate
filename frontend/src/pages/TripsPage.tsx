import { useState, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { clsx } from 'clsx';
import { Button, Card, Skeleton } from '../components/ui';
import CityMapPicker from '../components/CityMapPicker';
import { tripsApi, TripSearchParams, TripSortBy, TripSortOrder } from '../services/api/trips';
import { requestsApi } from '../services/api/requests';
import { useAuthStore } from '../stores/auth';
import type { Trip } from '../types';
import styles from './TripsPage.module.css';

type PreferenceKey = 'luggage_allowed' | 'smoking_allowed' | 'music_allowed' | 'pets_allowed';

interface PreferenceOption {
  key: PreferenceKey;
  label: string;
  icon: JSX.Element;
}

const PREFERENCES: PreferenceOption[] = [
  {
    key: 'luggage_allowed',
    label: 'Багаж',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="7" width="18" height="13" rx="2" />
        <path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
        <line x1="8" y1="11" x2="8" y2="20" />
        <line x1="16" y1="11" x2="16" y2="20" />
      </svg>
    ),
  },
  {
    key: 'smoking_allowed',
    label: 'Курение',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="13" width="14" height="6" rx="1" />
        <line x1="18" y1="13" x2="18" y2="19" />
        <line x1="22" y1="13" x2="22" y2="19" />
        <path d="M16 5c0 2 2 2 2 4" />
        <path d="M20 3c0 3 2 3 2 6" />
      </svg>
    ),
  },
  {
    key: 'music_allowed',
    label: 'Музыка',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 18V5l12-2v13" />
        <circle cx="6" cy="18" r="3" />
        <circle cx="18" cy="16" r="3" />
      </svg>
    ),
  },
  {
    key: 'pets_allowed',
    label: 'Питомцы',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="4" r="2" />
        <circle cx="18" cy="8" r="2" />
        <circle cx="20" cy="14" r="2" />
        <circle cx="4" cy="8" r="2" />
        <circle cx="6" cy="14" r="2" />
        <path d="M8 22c0-4.5 8-4.5 8 0z" />
      </svg>
    ),
  },
];

interface SortOption {
  id: string;
  label: string;
  sort_by: TripSortBy;
  sort_order: TripSortOrder;
}

const SORT_OPTIONS: SortOption[] = [
  { id: 'time-asc', label: 'Раньше отправление', sort_by: 'departure_time', sort_order: 'asc' },
  { id: 'time-desc', label: 'Позже отправление', sort_by: 'departure_time', sort_order: 'desc' },
  { id: 'price-asc', label: 'Сначала дешевле', sort_by: 'price', sort_order: 'asc' },
  { id: 'price-desc', label: 'Сначала дороже', sort_by: 'price', sort_order: 'desc' },
  { id: 'rating-desc', label: 'По рейтингу водителя', sort_by: 'driver_rating', sort_order: 'desc' },
];

const DEFAULT_SORT_ID = 'time-asc';

function getSortId(sortBy?: TripSortBy, sortOrder?: TripSortOrder): string {
  const match = SORT_OPTIONS.find(
    (option) => option.sort_by === sortBy && option.sort_order === sortOrder,
  );
  return match?.id ?? DEFAULT_SORT_ID;
}

function getSortOption(id: string): SortOption {
  return SORT_OPTIONS.find((option) => option.id === id) ?? SORT_OPTIONS[0];
}

function parseNumberOrUndefined(value: string | null): number | undefined {
  if (value === null || value === '') return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function parsePreference(value: string | null): boolean | undefined {
  if (value === 'true') return true;
  if (value === 'false') return false;
  return undefined;
}

function buildSearchParamsFromUrl(urlSearchParams: URLSearchParams): TripSearchParams {
  return {
    from_city: urlSearchParams.get('from_city') || undefined,
    to_city: urlSearchParams.get('to_city') || undefined,
    date: urlSearchParams.get('date') || undefined,
    min_price: parseNumberOrUndefined(urlSearchParams.get('min_price')),
    max_price: parseNumberOrUndefined(urlSearchParams.get('max_price')),
    departure_time_start: urlSearchParams.get('departure_time_start') || undefined,
    departure_time_end: urlSearchParams.get('departure_time_end') || undefined,
    luggage_allowed: parsePreference(urlSearchParams.get('luggage_allowed')),
    smoking_allowed: parsePreference(urlSearchParams.get('smoking_allowed')),
    music_allowed: parsePreference(urlSearchParams.get('music_allowed')),
    pets_allowed: parsePreference(urlSearchParams.get('pets_allowed')),
    sort_by: (urlSearchParams.get('sort_by') as TripSortBy) || undefined,
    sort_order: (urlSearchParams.get('sort_order') as TripSortOrder) || undefined,
  };
}

function searchParamsToUrl(params: TripSearchParams): URLSearchParams {
  const url = new URLSearchParams();
  if (params.from_city) url.set('from_city', params.from_city);
  if (params.to_city) url.set('to_city', params.to_city);
  if (params.date) url.set('date', params.date);
  if (params.min_price !== undefined) url.set('min_price', String(params.min_price));
  if (params.max_price !== undefined) url.set('max_price', String(params.max_price));
  if (params.departure_time_start) url.set('departure_time_start', params.departure_time_start);
  if (params.departure_time_end) url.set('departure_time_end', params.departure_time_end);
  if (params.luggage_allowed !== undefined) url.set('luggage_allowed', String(params.luggage_allowed));
  if (params.smoking_allowed !== undefined) url.set('smoking_allowed', String(params.smoking_allowed));
  if (params.music_allowed !== undefined) url.set('music_allowed', String(params.music_allowed));
  if (params.pets_allowed !== undefined) url.set('pets_allowed', String(params.pets_allowed));
  if (params.sort_by) url.set('sort_by', params.sort_by);
  if (params.sort_order) url.set('sort_order', params.sort_order);
  return url;
}

export default function TripsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [urlSearchParams, setUrlSearchParams] = useSearchParams();
  const currentUser = useAuthStore((state) => state.user);

  const [searchParams, setSearchParams] = useState<TripSearchParams>(() => buildSearchParamsFromUrl(urlSearchParams));
  const [fromCityInput, setFromCityInput] = useState(() => urlSearchParams.get('from_city') || '');
  const [toCityInput, setToCityInput] = useState(() => urlSearchParams.get('to_city') || '');
  const [dateInput, setDateInput] = useState(() => urlSearchParams.get('date') || '');

  const [minPriceInput, setMinPriceInput] = useState(() => urlSearchParams.get('min_price') || '');
  const [maxPriceInput, setMaxPriceInput] = useState(() => urlSearchParams.get('max_price') || '');
  const [timeStartInput, setTimeStartInput] = useState(() => urlSearchParams.get('departure_time_start') || '');
  const [timeEndInput, setTimeEndInput] = useState(() => urlSearchParams.get('departure_time_end') || '');
  const [preferences, setPreferences] = useState<Record<PreferenceKey, boolean>>(() => ({
    luggage_allowed: parsePreference(urlSearchParams.get('luggage_allowed')) === true,
    smoking_allowed: parsePreference(urlSearchParams.get('smoking_allowed')) === true,
    music_allowed: parsePreference(urlSearchParams.get('music_allowed')) === true,
    pets_allowed: parsePreference(urlSearchParams.get('pets_allowed')) === true,
  }));
  const [sortId, setSortId] = useState(() =>
    getSortId(
      (urlSearchParams.get('sort_by') as TripSortBy) || undefined,
      (urlSearchParams.get('sort_order') as TripSortOrder) || undefined,
    ),
  );

  const [mapOpen, setMapOpen] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(() => {
    const url = urlSearchParams;
    return !!(
      url.get('min_price') ||
      url.get('max_price') ||
      url.get('departure_time_start') ||
      url.get('departure_time_end') ||
      url.get('luggage_allowed') ||
      url.get('smoking_allowed') ||
      url.get('music_allowed') ||
      url.get('pets_allowed')
    );
  });

  const { data: tripsData, isLoading, error } = useQuery({
    queryKey: ['trips', searchParams],
    queryFn: () => tripsApi.search(searchParams),
    enabled: true,
  });

  const { data: userRequests } = useQuery({
    queryKey: ['my-requests', 'active'],
    queryFn: () => requestsApi.getMyRequests(),
    enabled: !!currentUser,
  });

  const trips = tripsData?.items || [];

  const userTripIds = useMemo(() => {
    if (!userRequests) return new Set<string>();
    return new Set(
      userRequests
        .filter((req) => req.status === 'pending' || req.status === 'confirmed')
        .map((req) => req.trip_id),
    );
  }, [userRequests]);

  const buildSearchParamsFromInputs = (sortIdOverride?: string): TripSearchParams => {
    const sort = getSortOption(sortIdOverride ?? sortId);
    const minPrice = parseNumberOrUndefined(minPriceInput);
    const maxPrice = parseNumberOrUndefined(maxPriceInput);
    return {
      from_city: fromCityInput || undefined,
      to_city: toCityInput || undefined,
      date: dateInput || undefined,
      min_price: minPrice,
      max_price: maxPrice,
      departure_time_start: timeStartInput || undefined,
      departure_time_end: timeEndInput || undefined,
      luggage_allowed: preferences.luggage_allowed ? true : undefined,
      smoking_allowed: preferences.smoking_allowed ? true : undefined,
      music_allowed: preferences.music_allowed ? true : undefined,
      pets_allowed: preferences.pets_allowed ? true : undefined,
      sort_by: sort.sort_by,
      sort_order: sort.sort_order,
    };
  };

  const applyParams = (params: TripSearchParams) => {
    setSearchParams(params);
    setUrlSearchParams(searchParamsToUrl(params), { replace: true });
  };

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    applyParams(buildSearchParamsFromInputs());
  };

  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const nextId = e.target.value;
    setSortId(nextId);
    applyParams(buildSearchParamsFromInputs(nextId));
  };

  const togglePreference = (key: PreferenceKey) => {
    setPreferences((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSwap = () => {
    setFromCityInput(toCityInput);
    setToCityInput(fromCityInput);
  };

  const handleResetFilters = () => {
    setFromCityInput('');
    setToCityInput('');
    setDateInput('');
    setMinPriceInput('');
    setMaxPriceInput('');
    setTimeStartInput('');
    setTimeEndInput('');
    setPreferences({
      luggage_allowed: false,
      smoking_allowed: false,
      music_allowed: false,
      pets_allowed: false,
    });
    setSortId(DEFAULT_SORT_ID);
    setSearchParams({});
    setUrlSearchParams(new URLSearchParams(), { replace: true });
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'BYN',
      minimumFractionDigits: 0,
    }).format(price);
  };

  const getDriverName = (trip: Trip) => trip.driver?.name || 'Водитель';
  const getDriverRating = (trip: Trip) => trip.driver?.rating ?? trip.driver?.rating_average;

  const filteredTrips = trips.filter((trip: Trip) => {
    if (currentUser && trip.driver_id === currentUser.id) return false;
    if (userTripIds.has(trip.id)) return false;
    return true;
  });

  const activePreferences = PREFERENCES.filter((pref) => searchParams[pref.key] === true);
  const hasActiveFilters = !!(
    searchParams.from_city ||
    searchParams.to_city ||
    searchParams.date ||
    searchParams.min_price !== undefined ||
    searchParams.max_price !== undefined ||
    searchParams.departure_time_start ||
    searchParams.departure_time_end ||
    activePreferences.length > 0
  );

  const activeFilterChipsCount =
    (searchParams.min_price !== undefined ? 1 : 0) +
    (searchParams.max_price !== undefined ? 1 : 0) +
    (searchParams.departure_time_start ? 1 : 0) +
    (searchParams.departure_time_end ? 1 : 0) +
    activePreferences.length;

  return (
    <div className={styles.container}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>{t('trips.searchTitle')}</h1>
        <p className={styles.pageSubtitle}>
          Найдите попутчика по маршруту, дате, цене и условиям
        </p>
      </div>

      <Card className={styles.searchCard}>
        <form onSubmit={handleSearch} className={styles.searchForm}>
          <div className={styles.searchRow}>
            <div className={styles.fieldGroup}>
              <label htmlFor="from-city" className={styles.fieldLabel}>
                {t('trips.from')}
              </label>
              <div className={styles.inputWithIcon}>
                <span className={clsx(styles.inputIcon, styles.iconFrom)} aria-hidden>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                    <circle cx="12" cy="10" r="3" />
                  </svg>
                </span>
                <input
                  id="from-city"
                  type="text"
                  value={fromCityInput}
                  onChange={(e) => setFromCityInput(e.target.value)}
                  placeholder={t('trips.fromCityPlaceholder')}
                  className={styles.searchInput}
                  autoComplete="off"
                />
                {fromCityInput && (
                  <button
                    type="button"
                    onClick={() => setFromCityInput('')}
                    className={styles.clearButton}
                    aria-label="Очистить поле «Откуда»"
                  >
                    ×
                  </button>
                )}
              </div>
            </div>

            <button
              type="button"
              onClick={handleSwap}
              className={styles.swapButton}
              aria-label="Поменять города местами"
              title="Поменять местами"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="17 1 21 5 17 9" />
                <path d="M3 11V9a4 4 0 0 1 4-4h14" />
                <polyline points="7 23 3 19 7 15" />
                <path d="M21 13v2a4 4 0 0 1-4 4H3" />
              </svg>
            </button>

            <div className={styles.fieldGroup}>
              <label htmlFor="to-city" className={styles.fieldLabel}>
                {t('trips.to')}
              </label>
              <div className={styles.inputWithIcon}>
                <span className={clsx(styles.inputIcon, styles.iconTo)} aria-hidden>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                    <circle cx="12" cy="10" r="3" />
                  </svg>
                </span>
                <input
                  id="to-city"
                  type="text"
                  value={toCityInput}
                  onChange={(e) => setToCityInput(e.target.value)}
                  placeholder={t('trips.toCityPlaceholder')}
                  className={styles.searchInput}
                  autoComplete="off"
                />
                {toCityInput && (
                  <button
                    type="button"
                    onClick={() => setToCityInput('')}
                    className={styles.clearButton}
                    aria-label="Очистить поле «Куда»"
                  >
                    ×
                  </button>
                )}
              </div>
            </div>

            <div className={styles.fieldGroup}>
              <label htmlFor="date" className={styles.fieldLabel}>
                {t('trips.date')}
              </label>
              <div className={styles.inputWithIcon}>
                <span className={styles.inputIcon} aria-hidden>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                    <line x1="16" y1="2" x2="16" y2="6" />
                    <line x1="8" y1="2" x2="8" y2="6" />
                    <line x1="3" y1="10" x2="21" y2="10" />
                  </svg>
                </span>
                <input
                  id="date"
                  name="date"
                  type="date"
                  value={dateInput}
                  onChange={(e) => setDateInput(e.target.value)}
                  className={styles.searchInput}
                />
              </div>
            </div>

            <Button type="submit" variant="primary" size="lg" className={styles.searchButton}>
              {t('trips.search')}
            </Button>
          </div>

          <div className={styles.searchExtras}>
            <button
              type="button"
              className={clsx(styles.linkButton, filtersOpen && styles.linkButtonActive)}
              onClick={() => setFiltersOpen((v) => !v)}
              aria-expanded={filtersOpen}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="4" y1="21" x2="4" y2="14" />
                <line x1="4" y1="10" x2="4" y2="3" />
                <line x1="12" y1="21" x2="12" y2="12" />
                <line x1="12" y1="8" x2="12" y2="3" />
                <line x1="20" y1="21" x2="20" y2="16" />
                <line x1="20" y1="12" x2="20" y2="3" />
                <line x1="1" y1="14" x2="7" y2="14" />
                <line x1="9" y1="8" x2="15" y2="8" />
                <line x1="17" y1="16" x2="23" y2="16" />
              </svg>
              {filtersOpen ? 'Скрыть фильтры' : 'Фильтры'}
              {activeFilterChipsCount > 0 && (
                <span className={styles.filterCounter}>{activeFilterChipsCount}</span>
              )}
            </button>
            <button
              type="button"
              className={styles.linkButton}
              onClick={() => setMapOpen((v) => !v)}
              aria-expanded={mapOpen}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" />
                <line x1="8" y1="2" x2="8" y2="18" />
                <line x1="16" y1="6" x2="16" y2="22" />
              </svg>
              {mapOpen ? 'Скрыть карту' : 'Подобрать на карте'}
            </button>
            {hasActiveFilters && (
              <button
                type="button"
                className={styles.linkButton}
                onClick={handleResetFilters}
              >
                Сбросить всё
              </button>
            )}
          </div>

          {filtersOpen && (
            <div className={styles.filtersPanel}>
              <div className={styles.filterGroup}>
                <div className={styles.filterTitle}>Цена за место, BYN</div>
                <div className={styles.rangeRow}>
                  <div className={styles.rangeField}>
                    <span className={styles.rangePrefix}>от</span>
                    <input
                      type="number"
                      min={0}
                      step={1}
                      placeholder="0"
                      value={minPriceInput}
                      onChange={(e) => setMinPriceInput(e.target.value)}
                      className={styles.rangeInput}
                      inputMode="decimal"
                    />
                  </div>
                  <div className={styles.rangeField}>
                    <span className={styles.rangePrefix}>до</span>
                    <input
                      type="number"
                      min={0}
                      step={1}
                      placeholder="∞"
                      value={maxPriceInput}
                      onChange={(e) => setMaxPriceInput(e.target.value)}
                      className={styles.rangeInput}
                      inputMode="decimal"
                    />
                  </div>
                </div>
              </div>

              <div className={styles.filterGroup}>
                <div className={styles.filterTitle}>Время отправления</div>
                <div className={styles.rangeRow}>
                  <div className={styles.rangeField}>
                    <span className={styles.rangePrefix}>с</span>
                    <input
                      type="time"
                      value={timeStartInput}
                      onChange={(e) => setTimeStartInput(e.target.value)}
                      className={styles.rangeInput}
                    />
                  </div>
                  <div className={styles.rangeField}>
                    <span className={styles.rangePrefix}>до</span>
                    <input
                      type="time"
                      value={timeEndInput}
                      onChange={(e) => setTimeEndInput(e.target.value)}
                      className={styles.rangeInput}
                    />
                  </div>
                </div>
              </div>

              <div className={clsx(styles.filterGroup, styles.filterGroupWide)}>
                <div className={styles.filterTitle}>Пометки</div>
                <div className={styles.preferencesRow}>
                  {PREFERENCES.map((pref) => {
                    const isActive = preferences[pref.key];
                    return (
                      <button
                        key={pref.key}
                        type="button"
                        className={clsx(styles.preferenceChip, isActive && styles.preferenceChipActive)}
                        onClick={() => togglePreference(pref.key)}
                        aria-pressed={isActive}
                      >
                        <span className={styles.preferenceIcon}>{pref.icon}</span>
                        {pref.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className={styles.filterActions}>
                <Button type="submit" variant="primary" size="md">
                  Применить фильтры
                </Button>
              </div>
            </div>
          )}

          {mapOpen && (
            <div className={styles.mapContainer}>
              <CityMapPicker
                fromCity={fromCityInput}
                toCity={toCityInput}
                onFromCityChange={setFromCityInput}
                onToCityChange={setToCityInput}
              />
            </div>
          )}
        </form>
      </Card>

      <div className={styles.resultsSection}>
        <div className={styles.resultsHeader}>
          <div className={styles.resultsHeaderTop}>
            <h2 className={styles.resultsTitle}>
              {isLoading
                ? 'Ищем поездки…'
                : filteredTrips.length > 0
                  ? `${filteredTrips.length} ${t('trips.found')}`
                  : t('trips.noResults')}
            </h2>
            <label className={styles.sortControl}>
              <span className={styles.sortLabel}>Сортировка:</span>
              <select
                value={sortId}
                onChange={handleSortChange}
                className={styles.sortSelect}
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {hasActiveFilters && !isLoading && (
            <div className={styles.activeFilters}>
              {searchParams.from_city && (
                <span className={styles.filterPill}>
                  <span className={styles.filterPillLabel}>Откуда:</span> {searchParams.from_city}
                </span>
              )}
              {searchParams.to_city && (
                <span className={styles.filterPill}>
                  <span className={styles.filterPillLabel}>Куда:</span> {searchParams.to_city}
                </span>
              )}
              {searchParams.date && (
                <span className={styles.filterPill}>
                  <span className={styles.filterPillLabel}>Дата:</span> {searchParams.date}
                </span>
              )}
              {(searchParams.min_price !== undefined || searchParams.max_price !== undefined) && (
                <span className={styles.filterPill}>
                  <span className={styles.filterPillLabel}>Цена:</span>{' '}
                  {searchParams.min_price !== undefined ? `${searchParams.min_price}` : '0'}
                  {' – '}
                  {searchParams.max_price !== undefined ? `${searchParams.max_price}` : '∞'} BYN
                </span>
              )}
              {(searchParams.departure_time_start || searchParams.departure_time_end) && (
                <span className={styles.filterPill}>
                  <span className={styles.filterPillLabel}>Время:</span>{' '}
                  {searchParams.departure_time_start || '00:00'}
                  {' – '}
                  {searchParams.departure_time_end || '23:59'}
                </span>
              )}
              {activePreferences.map((pref) => (
                <span key={pref.key} className={styles.filterPill}>
                  {pref.label}
                </span>
              ))}
            </div>
          )}
        </div>

        {error && (
          <div className={styles.error}>
            {t('errors.loadTrips')}
          </div>
        )}

        {isLoading && (
          <div className={styles.tripsList}>
            {[1, 2, 3].map((i) => (
              <Card key={i} className={styles.tripCard}>
                <div className={styles.tripHeader}>
                  <Skeleton variant="text" width="40%" height={24} />
                  <Skeleton variant="text" width="20%" height={24} />
                </div>
                <div className={styles.tripRoute}>
                  <Skeleton variant="text" width="30%" />
                  <Skeleton variant="text" width="30%" />
                </div>
                <div className={styles.tripFooter}>
                  <Skeleton variant="text" width="25%" />
                  <Skeleton variant="rounded" width={100} height={36} />
                </div>
              </Card>
            ))}
          </div>
        )}

        {!isLoading && filteredTrips.length === 0 && !error && (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon} aria-hidden>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </div>
            <p className={styles.emptyTitle}>{t('trips.noTrips')}</p>
            <p className={styles.emptyHint}>
              Попробуйте изменить параметры поиска или очистить фильтры.
            </p>
            {hasActiveFilters && (
              <Button variant="outline" onClick={handleResetFilters}>
                Сбросить всё
              </Button>
            )}
          </div>
        )}

        {!isLoading && filteredTrips.length > 0 && (
          <div className={styles.tripsList}>
            {filteredTrips.map((trip: Trip) => {
              const tripPrefs = PREFERENCES.filter((pref) => trip[pref.key]);
              return (
                <Card
                  key={trip.id}
                  className={styles.tripCard}
                  onClick={() => navigate(`/trips/${trip.id}`)}
                >
                  <div className={styles.tripHeader}>
                    <div className={styles.driverInfo}>
                      {trip.driver?.avatar_url && (
                        <img
                          src={trip.driver.avatar_url}
                          alt={getDriverName(trip)}
                          className={styles.driverAvatar}
                        />
                      )}
                      <span className={styles.driverName}>{getDriverName(trip)}</span>
                      {getDriverRating(trip) !== undefined && (
                        <span className={styles.driverRating}>
                          ★ {getDriverRating(trip)?.toFixed(1)}
                        </span>
                      )}
                    </div>
                    <div className={styles.tripPrice}>{formatPrice(trip.price_per_seat)}</div>
                  </div>

                  <div className={styles.tripRoute}>
                    <div className={styles.routePoint}>
                      <div className={styles.routeTime}>
                        {formatDate(trip.departure_date + 'T' + trip.departure_time_start)}
                      </div>
                      <div className={styles.routeLocation}>{trip.from_address || trip.from_city}</div>
                    </div>
                    <div className={styles.routeArrow}>→</div>
                    <div className={styles.routePoint}>
                      <div className={styles.routeTime}>
                        {trip.arrival_time
                          ? formatDate(trip.departure_date + 'T' + trip.arrival_time)
                          : '—'}
                      </div>
                      <div className={styles.routeLocation}>{trip.to_address || trip.to_city}</div>
                    </div>
                  </div>

                  {tripPrefs.length > 0 && (
                    <div className={styles.tripBadges}>
                      {tripPrefs.map((pref) => (
                        <span key={pref.key} className={styles.tripBadge} title={pref.label}>
                          <span className={styles.tripBadgeIcon}>{pref.icon}</span>
                          {pref.label}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className={styles.tripFooter}>
                    <div className={styles.tripInfo}>
                      <span>
                        {trip.available_seats} {t('trips.seats')}
                      </span>
                    </div>
                    <Button variant="outline" size="sm">
                      {t('trips.viewDetails')}
                    </Button>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
