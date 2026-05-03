import { useState, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { Button, Card, Input, Skeleton } from '../components/ui';
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
    setSearchParams(prev => ({ ...prev, from_city: city || undefined }));
  };

  const handleToCityChange = (city: string) => {
    setToCityInput(city);
    setSearchParams(prev => ({ ...prev, to_city: city || undefined }));
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

  return (
    <div className={styles.container}>
      <div className={styles.searchSection}>
        <Card className={styles.searchCard}>
          <CityMapPicker
            fromCity={fromCityInput}
            toCity={toCityInput}
            onFromCityChange={handleFromCityChange}
            onToCityChange={handleToCityChange}
          />
          <form onSubmit={handleSearch} className={styles.searchForm}>
            <div className={styles.searchInputs}>
              <Input
                name="date"
                type="date"
                label={t('trips.date')}
                value={dateInput}
                onChange={(e) => setDateInput(e.target.value)}
              />
            </div>
            <Button type="submit" variant="primary">
              {t('trips.search')}
            </Button>
          </form>
        </Card>
      </div>

      <div className={styles.resultsSection}>
        <h2 className={styles.resultsTitle}>
          {filteredTrips.length > 0 ? `${filteredTrips.length} ${t('trips.found')}` : t('trips.noResults')}
        </h2>

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

        {!isLoading && filteredTrips.length === 0 && (
          <div className={styles.noResults}>
            {t('trips.noTripsYet')}
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
                  <Button variant="primary" size="sm">
                    {t('trips.book')}
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