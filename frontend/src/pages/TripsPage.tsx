import { useState, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { clsx } from 'clsx';
import { Button, Card, Skeleton } from '../components/ui';
import CityMapPicker from '../components/CityMapPicker';
import { tripsApi, TripSearchParams } from '../services/api/trips';
import { requestsApi } from '../services/api/requests';
import { useAuthStore } from '../stores/auth';
import type { Trip } from '../types';
import styles from './TripsPage.module.css';

export default function TripsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [urlSearchParams, setUrlSearchParams] = useSearchParams();
  const currentUser = useAuthStore((state) => state.user);
  const [searchParams, setSearchParams] = useState<TripSearchParams>(() => ({
    from_city: urlSearchParams.get('from_city') || undefined,
    to_city: urlSearchParams.get('to_city') || undefined,
    date: urlSearchParams.get('date') || undefined,
  }));
  const [fromCityInput, setFromCityInput] = useState(() => urlSearchParams.get('from_city') || '');
  const [toCityInput, setToCityInput] = useState(() => urlSearchParams.get('to_city') || '');
  const [dateInput, setDateInput] = useState(() => urlSearchParams.get('date') || '');
  const [mapOpen, setMapOpen] = useState(false);

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
        .filter(req => req.status === 'pending' || req.status === 'confirmed')
        .map(req => req.trip_id)
    );
  }, [userRequests]);

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const nextParams: TripSearchParams = {
      from_city: fromCityInput || undefined,
      to_city: toCityInput || undefined,
      date: dateInput || undefined,
    };
    setSearchParams(nextParams);
    const next = new URLSearchParams();
    if (nextParams.from_city) next.set('from_city', nextParams.from_city);
    if (nextParams.to_city) next.set('to_city', nextParams.to_city);
    if (nextParams.date) next.set('date', nextParams.date);
    setUrlSearchParams(next, { replace: true });
  };

  const handleFromCityChange = (city: string) => {
    setFromCityInput(city);
  };

  const handleToCityChange = (city: string) => {
    setToCityInput(city);
  };

  const handleSwap = () => {
    setFromCityInput(toCityInput);
    setToCityInput(fromCityInput);
  };

  const handleResetFilters = () => {
    setFromCityInput('');
    setToCityInput('');
    setDateInput('');
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

  const getDriverName = (trip: Trip) => {
    return trip.driver?.name || 'Водитель';
  };

  const getDriverRating = (trip: Trip) => {
    return trip.driver?.rating ?? trip.driver?.rating_average;
  };

  const filteredTrips = trips.filter((trip: Trip) => {
    if (currentUser && trip.driver_id === currentUser.id) return false;
    if (userTripIds.has(trip.id)) return false;
    return true;
  });

  const hasActiveFilters = !!(searchParams.from_city || searchParams.to_city || searchParams.date);

  return (
    <div className={styles.container}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>{t('trips.searchTitle')}</h1>
        <p className={styles.pageSubtitle}>
          Найдите попутчика по маршруту и дате
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
                  onChange={(e) => handleFromCityChange(e.target.value)}
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
                  onChange={(e) => handleToCityChange(e.target.value)}
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

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className={styles.searchButton}
            >
              {t('trips.search')}
            </Button>
          </div>

          <div className={styles.searchExtras}>
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
                Сбросить фильтры
              </button>
            )}
          </div>

          {mapOpen && (
            <div className={styles.mapContainer}>
              <CityMapPicker
                fromCity={fromCityInput}
                toCity={toCityInput}
                onFromCityChange={handleFromCityChange}
                onToCityChange={handleToCityChange}
              />
            </div>
          )}
        </form>
      </Card>

      <div className={styles.resultsSection}>
        <div className={styles.resultsHeader}>
          <h2 className={styles.resultsTitle}>
            {isLoading
              ? 'Ищем поездки…'
              : filteredTrips.length > 0
                ? `${filteredTrips.length} ${t('trips.found')}`
                : t('trips.noResults')}
          </h2>
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
                Сбросить фильтры
              </Button>
            )}
          </div>
        )}

        {!isLoading && filteredTrips.length > 0 && (
          <div className={styles.tripsList}>
            {filteredTrips.map((trip: Trip) => (
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
                    <span className={styles.driverName}>
                      {getDriverName(trip)}
                    </span>
                    {getDriverRating(trip) !== undefined && (
                      <span className={styles.driverRating}>
                        ★ {getDriverRating(trip)?.toFixed(1)}
                      </span>
                    )}
                  </div>
                  <div className={styles.tripPrice}>
                    {formatPrice(trip.price_per_seat)}
                  </div>
                </div>

                <div className={styles.tripRoute}>
                  <div className={styles.routePoint}>
                    <div className={styles.routeTime}>{formatDate(trip.departure_date + 'T' + trip.departure_time_start)}</div>
                    <div className={styles.routeLocation}>{trip.from_address || trip.from_city}</div>
                  </div>
                  <div className={styles.routeArrow}>→</div>
                  <div className={styles.routePoint}>
                    <div className={styles.routeTime}>{trip.arrival_time ? formatDate(trip.departure_date + 'T' + trip.arrival_time) : '—'}</div>
                    <div className={styles.routeLocation}>{trip.to_address || trip.to_city}</div>
                  </div>
                </div>

                <div className={styles.tripFooter}>
                  <div className={styles.tripInfo}>
                    <span>{trip.available_seats} {t('trips.seats')}</span>
                  </div>
                  <Button variant="outline" size="sm">
                    {t('trips.viewDetails')}
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
