import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { Button, Card, Skeleton } from '../components/ui';
import { tripsApi } from '../services/api/trips';
import type { Trip } from '../types';
import styles from './MyTripsPage.module.css';

export default function MyTripsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<string>('');

  const { data: trips, isLoading, error } = useQuery({
    queryKey: ['myTrips', statusFilter],
    queryFn: () => tripsApi.getMyTrips(statusFilter || undefined),
  });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'long',
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

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { label: string; className: string }> = {
      draft: { label: t('trips.status.draft'), className: styles.statusDraft },
      published: { label: t('trips.status.published'), className: styles.statusPublished },
      active: { label: t('trips.status.active'), className: styles.statusActive },
      completed: { label: t('trips.status.completed'), className: styles.statusCompleted },
      cancelled: { label: t('trips.status.cancelled'), className: styles.statusCancelled },
    };
    const statusInfo = statusMap[status] || { label: status, className: '' };
    return <span className={`${styles.statusBadge} ${statusInfo.className}`}>{statusInfo.label}</span>;
  };

  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h1>{t('trips.myTrips')}</h1>
          <Button variant="primary" onClick={() => navigate('/trips/new')}>
            {t('trips.createTrip')}
          </Button>
        </div>
        <div className={styles.tripsList}>
          {[1, 2, 3].map((i) => (
            <Card key={i} className={styles.tripCard}>
              <Skeleton variant="text" width="60%" height={24} />
              <Skeleton variant="text" width="40%" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>{t('trips.myTrips')}</h1>
        <Button variant="primary" onClick={() => navigate('/trips/new')}>
          {t('trips.createTrip')}
        </Button>
      </div>

      <div className={styles.filterSection}>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className={styles.filterSelect}
        >
          <option value="">{t('trips.allStatuses')}</option>
          <option value="draft">{t('trips.status.draft')}</option>
          <option value="published">{t('trips.status.published')}</option>
          <option value="active">{t('trips.status.active')}</option>
          <option value="completed">{t('trips.status.completed')}</option>
          <option value="cancelled">{t('trips.status.cancelled')}</option>
        </select>
      </div>

      {error && (
        <div className={styles.error}>
          {t('errors.loadTrips')}
        </div>
      )}

      {trips && trips.length === 0 && (
        <div className={styles.emptyState}>
          <p>{t('trips.noTripsYet')}</p>
          <Button variant="primary" onClick={() => navigate('/trips/new')}>
            {t('trips.createFirstTrip')}
          </Button>
        </div>
      )}

      {trips && trips.length > 0 && (
        <div className={styles.tripsList}>
          {trips.map((trip: Trip) => (
            <Card 
              key={trip.id} 
              className={styles.tripCard}
              onClick={() => navigate(`/trips/${trip.id}`)}
            >
              <div className={styles.tripHeader}>
                <div className={styles.routeInfo}>
                  <span className={styles.cityName}>{trip.from_city}</span>
                  <span className={styles.routeArrow}>→</span>
                  <span className={styles.cityName}>{trip.to_city}</span>
                </div>
                {getStatusBadge(trip.status)}
              </div>

              <div className={styles.tripRoute}>
                <div className={styles.routePoint}>
                  <div className={styles.routeTime}>{formatDate(trip.departure_date + 'T' + trip.departure_time_start)}</div>
                  <div className={styles.routeLocation}>{trip.from_address || trip.from_city}</div>
                </div>
                <div className={styles.routeArrow}>→</div>
                <div className={styles.routePoint}>
                  <div className={styles.routeLocation}>{trip.to_address || trip.to_city}</div>
                </div>
              </div>

              <div className={styles.tripFooter}>
                <div className={styles.tripInfo}>
                  <span>{trip.available_seats} {t('trips.seats')}</span>
                  <span className={styles.tripPrice}>{formatPrice(trip.price_per_seat)}</span>
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
  );
}
