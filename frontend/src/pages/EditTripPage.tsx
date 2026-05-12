import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Button, Card, Input, Modal, Skeleton } from '../components/ui';
import DatePickerInput from '../components/DatePickerInput';
import { tripsApi } from '../services/api/trips';
import { useAuthStore } from '../stores/auth';
import type { TripFormData } from '../types';
import styles from './NewTripPage.module.css';

export default function EditTripPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const currentUser = useAuthStore((state) => state.user);

  const [formData, setFormData] = useState<TripFormData>({
    from_city: '',
    from_address: '',
    to_city: '',
    to_address: '',
    departure_date: '',
    departure_time_start: '',
    departure_time_end: '',
    is_time_range: false,
    arrival_time: '',
    price_per_seat: 0,
    total_seats: 1,
    description: '',
    luggage_allowed: true,
    smoking_allowed: false,
    music_allowed: true,
    pets_allowed: false,
    car_model: '',
    car_color: '',
    car_license_plate: '',
  });

  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load trip data
  const { data: trip, isLoading, isError } = useQuery({
    queryKey: ['trip', id],
    queryFn: () => tripsApi.getById(id!),
    enabled: !!id,
  });

  // Populate form when trip data is loaded
  useEffect(() => {
    if (trip) {
      // Check ownership
      if (currentUser?.id !== trip.driver_id) {
        navigate(`/trips/${id}`);
        return;
      }

      setFormData({
        from_city: trip.from_city || '',
        from_address: trip.from_address || '',
        to_city: trip.to_city || '',
        to_address: trip.to_address || '',
        departure_date: trip.departure_date || '',
        departure_time_start: trip.departure_time_start || '',
        departure_time_end: trip.departure_time_end || '',
        is_time_range: trip.is_time_range || false,
        arrival_time: trip.arrival_time || '',
        price_per_seat: trip.price_per_seat || 0,
        total_seats: trip.total_seats || 1,
        description: trip.description || '',
        luggage_allowed: trip.luggage_allowed ?? true,
        smoking_allowed: trip.smoking_allowed ?? false,
        music_allowed: trip.music_allowed ?? true,
        pets_allowed: trip.pets_allowed ?? false,
        car_model: trip.car_model || '',
        car_color: trip.car_color || '',
        car_license_plate: trip.car_license_plate || '',
      });
    }
  }, [trip, currentUser?.id, id, navigate]);

  const updateTripMutation = useMutation({
    mutationFn: (data: Partial<TripFormData>) => tripsApi.update(id!, data),
    onSuccess: () => {
      setShowSuccessModal(true);
    },
    onError: (e: any) => {
      // Handle different error types
      let errorMessage = t('errors.updateTrip');
      
      if (e?.response?.data?.detail) {
        errorMessage = e.response.data.detail;
      } else if (e?.message) {
        errorMessage = e.message;
      } else if (e?.statusText) {
        errorMessage = `${t('errors.statusCode')} ${e.status} - ${e.statusText}`;
      } else if (typeof e === 'string') {
        errorMessage = e;
      }
      
      setError(errorMessage);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    updateTripMutation.mutate({
      ...formData,
      departure_time_end: formData.is_time_range ? formData.departure_time_end || undefined : undefined,
      arrival_time: formData.arrival_time || undefined,
      from_address: formData.from_address || undefined,
      to_address: formData.to_address || undefined,
      description: formData.description || undefined,
      car_model: formData.car_model || undefined,
      car_color: formData.car_color || undefined,
      car_license_plate: formData.car_license_plate || undefined,
    });
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? Number(value) : value,
    }));
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: checked,
    }));
  };

  if (isLoading) {
    return (
      <div className={styles.container}>
        <Card className={styles.card}>
          <Skeleton variant="text" width="60%" height={32} />
          <Skeleton variant="text" width="40%" />
          <Skeleton variant="rounded" height={200} />
        </Card>
      </div>
    );
  }

  if (isError || !trip) {
    return (
      <div className={styles.container}>
        <Card className={styles.card}>
          <div className={styles.error}>{t('errors.tripNotFound')}</div>
          <Button onClick={() => navigate('/trips/my')}>{t('trips.backToMyTrips')}</Button>
        </Card>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <Card className={styles.card}>
        <h1 className={styles.title}>{t('trips.editTrip')}</h1>

        <form onSubmit={handleSubmit} className={styles.form}>
          {/* Route Section */}
          <div className={styles.section} data-route>
            <h2 className={styles.sectionTitle}>{t('trips.route')}</h2>
            
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label htmlFor="from_city">{t('trips.fromCity')} *</label>
                <Input
                  id="from_city"
                  name="from_city"
                  value={formData.from_city}
                  onChange={handleChange}
                  required
                  placeholder={t('trips.fromCityPlaceholder')}
                />
              </div>
              <div className={styles.formGroup}>
                <label htmlFor="from_address">{t('trips.fromAddress')}</label>
                <Input
                  id="from_address"
                  name="from_address"
                  value={formData.from_address}
                  onChange={handleChange}
                  placeholder={t('trips.fromAddressPlaceholder')}
                />
              </div>
            </div>

            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label htmlFor="to_city">{t('trips.toCity')} *</label>
                <Input
                  id="to_city"
                  name="to_city"
                  value={formData.to_city}
                  onChange={handleChange}
                  required
                  placeholder={t('trips.toCityPlaceholder')}
                />
              </div>
              <div className={styles.formGroup}>
                <label htmlFor="to_address">{t('trips.toAddress')}</label>
                <Input
                  id="to_address"
                  name="to_address"
                  value={formData.to_address}
                  onChange={handleChange}
                  placeholder={t('trips.toAddressPlaceholder')}
                />
              </div>
            </div>
          </div>

          {/* Time Section */}
          <div className={styles.section} data-schedule>
            <h2 className={styles.sectionTitle}>{t('trips.schedule')}</h2>
            
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label htmlFor="departure_date">{t('trips.departureDate')} *</label>
                <DatePickerInput
                  id="departure_date"
                  value={formData.departure_date}
                  onChange={(v) =>
                    setFormData((prev) => ({ ...prev, departure_date: v }))
                  }
                  placeholder={t('trips.departureDate')}
                  ariaLabel={t('trips.departureDate')}
                />
              </div>
              <div className={styles.formGroup}>
                <label htmlFor="departure_time_start">{t('trips.departureTime')} *</label>
                <Input
                  id="departure_time_start"
                  name="departure_time_start"
                  type="time"
                  value={formData.departure_time_start}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className={styles.checkboxGroup}>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  name="is_time_range"
                  checked={formData.is_time_range}
                  onChange={handleCheckboxChange}
                />
                <span>{t('trips.isTimeRange')}</span>
              </label>
            </div>

            {formData.is_time_range && (
              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label htmlFor="departure_time_end">{t('trips.departureTimeEnd')}</label>
                  <Input
                    id="departure_time_end"
                    name="departure_time_end"
                    type="time"
                    value={formData.departure_time_end}
                    onChange={handleChange}
                  />
                </div>
              </div>
            )}

            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label htmlFor="arrival_time">{t('trips.arrivalTime')}</label>
                <Input
                  id="arrival_time"
                  name="arrival_time"
                  type="time"
                  value={formData.arrival_time}
                  onChange={handleChange}
                />
              </div>
            </div>
          </div>

          {/* Price & Seats Section */}
          <div className={styles.section} data-price>
            <h2 className={styles.sectionTitle}>{t('trips.priceAndSeats')}</h2>
            
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label htmlFor="price_per_seat">{t('trips.pricePerSeat')} *</label>
                <Input
                  id="price_per_seat"
                  name="price_per_seat"
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={formData.price_per_seat}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label htmlFor="total_seats">{t('trips.totalSeats')} *</label>
                <Input
                  id="total_seats"
                  name="total_seats"
                  type="number"
                  min="1"
                  max="10"
                  value={formData.total_seats}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>
          </div>

          {/* Car Section */}
          <div className={styles.section} data-car>
            <h2 className={styles.sectionTitle}>{t('trips.carInfo')}</h2>
            
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label htmlFor="car_model">{t('trips.carModel')}</label>
                <Input
                  id="car_model"
                  name="car_model"
                  value={formData.car_model}
                  onChange={handleChange}
                  placeholder={t('trips.carModelPlaceholder')}
                />
              </div>
              <div className={styles.formGroup}>
                <label htmlFor="car_color">{t('trips.carColor')}</label>
                <Input
                  id="car_color"
                  name="car_color"
                  value={formData.car_color}
                  onChange={handleChange}
                  placeholder={t('trips.carColorPlaceholder')}
                />
              </div>
            </div>

            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label htmlFor="car_license_plate">{t('trips.licensePlate')}</label>
                <Input
                  id="car_license_plate"
                  name="car_license_plate"
                  value={formData.car_license_plate}
                  onChange={handleChange}
                  placeholder={t('trips.licensePlatePlaceholder')}
                />
              </div>
            </div>
          </div>

          {/* Preferences Section */}
          <div className={styles.section} data-preferences>
            <h2 className={styles.sectionTitle}>{t('trips.preferences')}</h2>
            
            <div className={styles.checkboxGrid}>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  name="luggage_allowed"
                  checked={formData.luggage_allowed}
                  onChange={handleCheckboxChange}
                />
                <span>{t('trips.luggageAllowed')}</span>
              </label>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  name="smoking_allowed"
                  checked={formData.smoking_allowed}
                  onChange={handleCheckboxChange}
                />
                <span>{t('trips.smokingAllowed')}</span>
              </label>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  name="music_allowed"
                  checked={formData.music_allowed}
                  onChange={handleCheckboxChange}
                />
                <span>{t('trips.musicAllowed')}</span>
              </label>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  name="pets_allowed"
                  checked={formData.pets_allowed}
                  onChange={handleCheckboxChange}
                />
                <span>{t('trips.petsAllowed')}</span>
              </label>
            </div>
          </div>

          {/* Description Section */}
          <div className={styles.section} data-description>
            <h2 className={styles.sectionTitle}>{t('trips.description')}</h2>
            
            <div className={styles.formGroup}>
              <label htmlFor="description">{t('trips.descriptionLabel')}</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                className={styles.textarea}
                rows={4}
                placeholder={t('trips.descriptionPlaceholder')}
              />
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className={styles.error}>
              {error}
            </div>
          )}

          {/* Actions */}
          <div className={styles.actions}>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate(`/trips/${id}`)}
            >
              {t('common.cancel')}
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={updateTripMutation.isPending}
            >
              {updateTripMutation.isPending ? t('common.saving') : t('trips.saveChanges')}
            </Button>
          </div>
        </form>
      </Card>

      {/* Success Modal */}
      <Modal
        isOpen={showSuccessModal}
        onClose={() => {
          setShowSuccessModal(false);
          navigate(`/trips/${id}`);
        }}
        title={t('trips.updateSuccessTitle')}
      >
        <div className={styles.successContent}>
          <div className={styles.successIcon}>✓</div>
          <p className={styles.successMessage}>{t('trips.updateSuccessMessage')}</p>
          <div className={styles.successActions}>
            <Button variant="primary" onClick={() => {
              setShowSuccessModal(false);
              navigate(`/trips/${id}`);
            }}>
              {t('trips.viewTrip')}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}