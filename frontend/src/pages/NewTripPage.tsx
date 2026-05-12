import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { Button, Card, Input, Modal } from '../components/ui';
import DatePickerInput from '../components/DatePickerInput';
import { tripsApi } from '../services/api/trips';
import type { TripFormData, Trip } from '../types';
import styles from './NewTripPage.module.css';



export default function NewTripPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
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
  const [createdTrip, setCreatedTrip] = useState<Trip | null>(null);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [priceInputRaw, setPriceInputRaw] = useState<string>('0');
  const [seatsInputRaw, setSeatsInputRaw] = useState<string>('1');
  const [arrivalAcknowledgedDifferentDay, setArrivalAcknowledgedDifferentDay] = useState(false);

  const arrivalBeforeDeparture =
    !!formData.arrival_time &&
    !!formData.departure_time_start &&
    formData.arrival_time < formData.departure_time_start;
  const showArrivalWarning =
    arrivalBeforeDeparture && !arrivalAcknowledgedDifferentDay;

  useEffect(() => {
    if (!arrivalBeforeDeparture && arrivalAcknowledgedDifferentDay) {
      setArrivalAcknowledgedDifferentDay(false);
    }
  }, [arrivalBeforeDeparture, arrivalAcknowledgedDifferentDay]);

  const createTripMutation = useMutation({
    mutationFn: (data: TripFormData) => tripsApi.create(data),
    onSuccess: (trip) => {
      setCreatedTrip(trip);
      setShowSuccessModal(true);
    },
  });

  const handleCloseModal = () => {
    setShowSuccessModal(false);
    if (createdTrip) {
      navigate(`/trips/${createdTrip.id}`);
    }
  };

  const handleViewTrip = () => {
    setShowSuccessModal(false);
    if (createdTrip) {
      navigate(`/trips/${createdTrip.id}`);
    }
  };

  const handleCreateAnother = () => {
    setShowSuccessModal(false);
    setCreatedTrip(null);
    setFormData({
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
    setPriceInputRaw('0');
    setSeatsInputRaw('1');
    setArrivalAcknowledgedDifferentDay(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (showArrivalWarning) return;
    createTripMutation.mutate({
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

  const handlePriceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = e.target;
    setPriceInputRaw(value);
    setFormData((prev) => ({
      ...prev,
      price_per_seat: value === '' ? 0 : Number(value),
    }));
  };

  const handleSeatsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = e.target;
    setSeatsInputRaw(value);
    setFormData((prev) => ({
      ...prev,
      total_seats: value === '' ? 0 : Number(value),
    }));
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

  return (
    <div className={styles.container}>
      <Card className={styles.card}>
        <h1 className={styles.title}>{t('trips.createNewTrip')}</h1>

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
                  minDate={new Date()}
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
                {showArrivalWarning && (
                  <div className={styles.fieldWarning}>
                    <div className={styles.fieldWarningMessage}>
                      {t('trips.arrivalBeforeDeparture')}
                    </div>
                    <button
                      type="button"
                      className={styles.fieldWarningButton}
                      onClick={() => setArrivalAcknowledgedDifferentDay(true)}
                    >
                      {t('trips.arrivalDifferentDayPrompt')}
                    </button>
                  </div>
                )}
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
                  min="0"
                  className={styles.noSpinner}
                  value={priceInputRaw}
                  onChange={handlePriceChange}
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
                  value={seatsInputRaw}
                  onChange={handleSeatsChange}
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
          {createTripMutation.isError && (
            <div className={styles.error}>
              {t('errors.createTrip')}
            </div>
          )}

          {/* Actions */}
          <div className={styles.actions}>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/trips/my')}
            >
              {t('common.cancel')}
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={createTripMutation.isPending}
            >
              {createTripMutation.isPending ? t('common.creating') : t('trips.createTrip')}
            </Button>
          </div>
        </form>
      </Card>

      {/* Success Modal */}
      <Modal
        isOpen={showSuccessModal}
        onClose={handleCloseModal}
        title={t('trips.successTitle')}
      >
        <div className={styles.successContent}>
          <div className={styles.successIcon}>✓</div>
          <p className={styles.successMessage}>{t('trips.successMessage')}</p>
          {createdTrip && (
            <div className={styles.tripInfo}>
              <p><strong>{createdTrip.from_city}</strong> → <strong>{createdTrip.to_city}</strong></p>
              <p>{createdTrip.departure_date}</p>
            </div>
          )}
          <div className={styles.successActions}>
            <Button variant="outline" onClick={handleCreateAnother}>
              {t('trips.createAnother')}
            </Button>
            <Button variant="primary" onClick={handleViewTrip}>
              {t('trips.viewTrip')}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
