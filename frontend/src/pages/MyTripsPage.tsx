import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { Button, Card, Skeleton } from '../components/ui';
import { tripsApi } from '../services/api/trips';
import type { Trip } from '../types';
import styles from './MyTripsPage.module.css';

type TabType = 'driver' | 'passenger';

export default function MyTripsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabType>('driver');
  const [statusFilter, setStatusFilter] = useState<string>('');

  const { data: driverTrips, isLoading: isDriverLoading } = useQuery({
    queryKey: ['myTrips', 'driver', statusFilter],
    queryFn: () => tripsApi.getMyTrips(statusFilter || undefined),
    enabled: activeTab === 'driver',
  });

  const { data: passengerTrips, isLoading: isPassengerLoading } = useQuery({
    queryKey: ['myTrips', 'passenger', statusFilter],
    queryFn: () => tripsApi.getMyPassengerTrips(statusFilter || undefined),
    enabled: activeTab === 'passenger',
  });

  const trips = activeTab === 'driver' ? driverTrips : passengerTrips;
  const isLoading = activeTab === 'driver' ? isDriverLoading : isPassengerLoading;

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

  const renderTripCard = (trip: Trip) => (
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
          <div className={styles.routeCity}>{trip.from_city}</div>
          {trip.from_address && <div className={styles.routeLocation}>{trip.from_address}</div>}
        </div>
        <div className={styles.routeArrow}>→</div>
        <div className={styles.routePoint}>
          <div className={styles.routeCity}>{trip.to_city}</div>
          {trip.to_address && <div className={styles.routeLocation}>{trip.to_address}</div>}
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
  );

  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h1>{t('trips.myTrips')}</h1>
          {activeTab === 'driver' && (
            <Button variant="primary" onClick={() => navigate('/trips/new')}>
              {t('trips.createTrip')}
            </Button>
          )}
        </div>
        
        <div className={styles.tabs}>
          <button 
            className={`${styles.tab} ${activeTab === 'driver' ? styles.tabActive : ''}`}
            onClick={() => setActiveTab('driver')}
          >
            {t('trips.asDriver')}
          </button>
          <button 
            className={`${styles.tab} ${activeTab === 'passenger' ? styles.tabActive : ''}`}
            onClick={() => setActiveTab('passenger')}
          >
            {t('trips.asPassenger')}
          </button>
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
        {activeTab === 'driver' && (
          <Button variant="primary" onClick={() => navigate('/trips/new')}>
            {t('trips.createTrip')}
          </Button>
        )}
      </div>

      <div className={styles.tabs}>
        <button 
          className={`${styles.tab} ${activeTab === 'driver' ? styles.tabActive : ''}`}
          onClick={() => setActiveTab('driver')}
        >
          {t('trips.asDriver')}
        </button>
        <button 
          className={`${styles.tab} ${activeTab === 'passenger' ? styles.tabActive : ''}`}
          onClick={() => setActiveTab('passenger')}
        >
          {t('trips.asPassenger')}
        </button>
      </div>

      <div className={styles.filterSection}>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className={styles.filterSelect}
        >
          <option value="">{t('trips.allStatuses')}</option>
          <option value="published">{t('trips.status.published')}</option>
          <option value="completed">{t('trips.status.completed')}</option>
          <option value="cancelled">{t('trips.status.cancelled')}</option>
        </select>
      </div>

      {activeTab === 'passenger' && passengerTrips && passengerTrips.length === 0 && (
        <div className={styles.emptyState}>
          <p>{t('trips.noPassengerTrips')}</p>
          <Button variant="primary" onClick={() => navigate('/trips')}>
            {t('trips.findTrips')}
          </Button>
        </div>
      )}

      {activeTab === 'driver' && driverTrips && driverTrips.length === 0 && (
        <div className={styles.emptyState}>
          <p>{t('trips.noTripsYet')}</p>
          <Button variant="primary" onClick={() => navigate('/trips/new')}>
            {t('trips.createFirstTrip')}
          </Button>
        </div>
      )}

      {trips && trips.length > 0 && (
        <div className={styles.tripsList}>
          {trips.map(renderTripCard)}
        </div>
      )}
    </div>
  );
}