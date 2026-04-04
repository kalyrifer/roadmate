import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { Button, Card, Input, Skeleton } from '../components/ui';
import CityMapPicker from '../components/CityMapPicker';
import { tripsApi, TripSearchParams } from '../services/api/trips';
import { useAuthStore } from '../stores/auth';
import type { Trip } from '../types';
import styles from './TripsPage.module.css';

export default function TripsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const currentUser = useAuthStore((state) => state.user);
  const [searchParams, setSearchParams] = useState<TripSearchParams>({});
  const [fromCityInput, setFromCityInput] = useState(searchParams.from_city || '');
  const [toCityInput, setToCityInput] = useState(searchParams.to_city || '');

  const { data: tripsData, isLoading, error } = useQuery({
    queryKey: ['trips', searchParams],
    queryFn: () => tripsApi.search(searchParams),
  });

  const trips = tripsData?.items || [];

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const dateValue = formData.get('date') as string;
    setSearchParams({
      from_city: fromCityInput || formData.get('from') as string || undefined,
      to_city: toCityInput || formData.get('to') as string || undefined,
      date: dateValue || undefined,
    });
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
                defaultValue={searchParams.date}
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
          {tripsData?.total ? `${tripsData.total} ${t('trips.found')}` : t('trips.noResults')}
        </h2>

        {!isLoading && trips.length > 0 && trips.filter((t: Trip) => !currentUser || t.driver_id !== currentUser.id).length === 0 && (
          <div className={styles.noResults}>
            {t('trips.noTripsYet')}
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

        {error && (
          <div className={styles.error}>
            {t('errors.loadTrips')}
          </div>
        )}

        {trips && trips.length > 0 && (
          <div className={styles.tripsList}>
            {trips
              .filter((trip: Trip) => !currentUser || trip.driver_id !== currentUser.id)
              .map((trip: Trip) => (
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
