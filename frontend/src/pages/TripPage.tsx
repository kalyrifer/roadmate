import { useParams, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Card, Input, Modal, Skeleton } from '../components/ui';
import { Toast, showToast } from '../components/ui/Toast';
import { tripsApi } from '../services/api/trips';
import { chatApi } from '../services/api/chat';
import { reviewsApi, usersApi } from '../services/api';
import { useAuthStore } from '../stores/auth';
import styles from './TripPage.module.css';

export default function TripPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const currentUser = useAuthStore((state) => state.user);

  console.log('TripPage auth debug:', {
    isAuthenticated,
    currentUser: currentUser,
  });

  const [isBookingModalOpen, setIsBookingModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedPassengerId, setSelectedPassengerId] = useState<string | null>(null);
  const [selectedDriverId, setSelectedDriverId] = useState<string | null>(null);
  const [seatsRequested, setSeatsRequested] = useState<number>(1);
  const [message, setMessage] = useState<string>('');
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
  const [reviewRating, setReviewRating] = useState<number>(5);
  const [reviewText, setReviewText] = useState<string>('');
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [reviewTargetId, setReviewTargetId] = useState<string | null>(null);
  const [reviewTargetName, setReviewTargetName] = useState<string>('');
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { data: trip, isLoading, error } = useQuery({
    queryKey: ['trip', id],
    queryFn: async () => {
      try {
        const result = await tripsApi.getById(id!);
        console.log('TripPage: Trip API response:', result);
        console.log('TripPage: Driver data:', result?.driver);
        console.log('TripPage: Available seats:', result?.available_seats);
        console.log('TripPage: Trip status:', result?.status);
        return result;
      } catch (err: any) {
        console.error('TripPage: Error loading trip:', err);
        console.error('TripPage: Error response:', err?.response?.data);
        console.error('TripPage: Error status:', err?.response?.status);
        throw err;
      }
    },
    enabled: !!id,
  });

  const { data: driverReviews } = useQuery({
    queryKey: ['driverReviews', trip?.driver_id],
    queryFn: async () => {
      if (!trip?.driver_id) return null;
      try {
        const result = await reviewsApi.getForUser(trip.driver_id);
        return result;
      } catch (err) {
        console.error('Error loading reviews:', err);
        return null;
      }
    },
    enabled: !!trip?.driver_id,
  });

  const { data: selectedDriverReviews } = useQuery({
    queryKey: ['userReviews', selectedDriverId],
    queryFn: async () => {
      if (!selectedDriverId) return null;
      try {
        return await reviewsApi.getForUser(selectedDriverId);
      } catch (err) {
        console.error('Error loading driver reviews:', err);
        return null;
      }
    },
    enabled: !!selectedDriverId,
  });

  const { data: selectedPassengerReviews } = useQuery({
    queryKey: ['userReviews', selectedPassengerId],
    queryFn: async () => {
      if (!selectedPassengerId) return null;
      try {
        return await reviewsApi.getForUser(selectedPassengerId);
      } catch (err) {
        console.error('Error loading passenger reviews:', err);
        return null;
      }
    },
    enabled: !!selectedPassengerId,
  });

  const { data: passengerProfile } = useQuery({
    queryKey: ['userProfile', selectedPassengerId],
    queryFn: async () => {
      if (!selectedPassengerId) return null;
      try {
        const result = await usersApi.getById(selectedPassengerId);
        return result;
      } catch (err) {
        console.error('Error loading passenger profile:', err);
        return null;
      }
    },
    enabled: !!selectedPassengerId,
  });

  const { data: driverProfile, isLoading: driverProfileLoading } = useQuery({
    queryKey: ['userProfile', selectedDriverId],
    queryFn: async () => {
      if (!selectedDriverId) return null;
      try {
        const result = await usersApi.getById(selectedDriverId);
        return result;
      } catch (err) {
        console.error('Error loading driver profile:', err);
        return null;
      }
    },
    enabled: !!selectedDriverId,
  });

  const { data: canReviewData } = useQuery({
    queryKey: ['canReview', id],
    queryFn: async () => {
      if (!id) return { can_review: false, reason: '' };
      try {
        const result = await reviewsApi.checkCanReview(id);
        return result;
      } catch (err) {
        console.error('Error checking can review:', err);
        return { can_review: false, reason: '' };
      }
    },
    enabled: !!id,
  });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      weekday: 'long',
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

  // All mutations must be defined at the top level, before any conditional returns
  const deleteTripMutation = useMutation({
    mutationFn: () => tripsApi.delete(id!),
    onSuccess: () => {
      setIsDeleteModalOpen(false);
      navigate('/trips/my');
    },
    onError: (e: any) => {
      setDeleteError(e?.response?.data?.detail || t('errors.deleteTrip'));
    },
  });

  const publishTripMutation = useMutation({
    mutationFn: () => tripsApi.publish(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trip', id] });
    },
  });

  const completeTripMutation = useMutation({
    mutationFn: () => tripsApi.complete(id!),
    onSuccess: () => {
      showToast(t('trips.completedSuccess'), 'success');
      queryClient.invalidateQueries({ queryKey: ['trip', id] });
    },
    onError: (e: any) => {
      showToast(e?.response?.data?.detail || t('errors.completeTrip'), 'error');
    },
  });

  const createBookingMutation = useMutation({
    mutationFn: async () => {
      setBookingError(null);
      return tripsApi.createRequest(id!, {
        seats_requested: seatsRequested,
        message: message.trim() ? message.trim() : undefined,
      });
    },
    onSuccess: () => {
      setIsBookingModalOpen(false);
      setMessage('');
      setSeatsRequested(1);
    },
    onError: (e: any) => {
      setBookingError(e?.response?.data?.detail || t('errors.serverError'));
    },
  });

  const openChatMutation = useMutation({
    mutationFn: () => chatApi.createOrGetConversation(id!, ''),
    onSuccess: (conversation) => {
      navigate(`/chat/${conversation.id}`);
    },
  });

  const createReviewMutation = useMutation({
    mutationFn: async () => {
      setReviewError(null);
      if (!id || !reviewTargetId) return;
      return reviewsApi.create({
        trip_id: id,
        target_id: reviewTargetId,
        rating: reviewRating,
        text: reviewText.trim() ? reviewText.trim() : undefined,
      });
    },
    onSuccess: () => {
      setIsReviewModalOpen(false);
      setReviewRating(5);
      setReviewText('');
      queryClient.invalidateQueries({ queryKey: ['driverReviews', trip?.driver_id] });
      if (reviewTargetId) {
        queryClient.invalidateQueries({ queryKey: ['userReviews', reviewTargetId] });
        queryClient.invalidateQueries({ queryKey: ['userProfile', reviewTargetId] });
      }
      queryClient.invalidateQueries({ queryKey: ['canReview', id] });
    },
    onError: (e: any) => {
      setReviewError(e?.response?.data?.detail || t('errors.serverError'));
    },
  });

  const openReviewModal = (targetUserId: string, targetName: string) => {
    setReviewTargetId(targetUserId);
    setReviewTargetName(targetName);
    setReviewRating(5);
    setReviewText('');
    setReviewError(null);
    setIsReviewModalOpen(true);
  };

  // Now handle conditional loading state
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

  // Handle error state
  if (error) {
    console.error('TripPage: Error state:', error);
    return (
      <div className={styles.container}>
        <Card className={styles.card}>
          <div className={styles.error}>Ошибка загрузки поездки: {String(error)}</div>
          <Button onClick={() => navigate('/trips')}>{t('trips.backToSearch')}</Button>
        </Card>
      </div>
    );
  }

  // Handle no trip data
  if (!trip) {
    return (
      <div className={styles.container}>
        <Card className={styles.card}>
          <div className={styles.error}>{t('errors.tripNotFound')}</div>
          <Button onClick={() => navigate('/trips')}>{t('trips.backToSearch')}</Button>
        </Card>
      </div>
    );
  }

  // Safe access to driver data with fallbacks
  const driverName = trip.driver?.name || trip.driver?.first_name || 'Водитель';
  const driverRating = trip.driver?.rating ?? trip.driver?.rating_average ?? trip.driver?.rating;
  const isOwner = isAuthenticated && currentUser?.id === trip.driver_id;
  const maxSeats = Math.min(8, trip.available_seats ?? 0);

  console.log('TripPage debug:', {
    isAuthenticated,
    currentUserId: currentUser?.id,
    tripDriverId: trip.driver_id,
    isOwner,
  });

  const openBooking = () => {
    setBookingError(null);
    setSeatsRequested(1);
    setMessage('');
    setIsBookingModalOpen(true);
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

  return (
    <div className={styles.container}>
      <Card className={styles.card}>
        <div className={styles.header}>
          <div>
            <h1 className={styles.title}>{t('trips.tripDetails')}</h1>
            {isOwner && <div className={styles.ownerBadge}>{getStatusBadge(trip.status)}</div>}
          </div>
          <div className={styles.price}>{formatPrice(trip.price_per_seat)}</div>
        </div>

        <div className={styles.route}>
          <div className={styles.routePoint}>
            <div className={styles.routeTime}>{formatDate(trip.departure_date + 'T' + trip.departure_time_start)}</div>
            <div className={styles.routeAddress}>{trip.from_address || trip.from_city}</div>
          </div>
          <div className={styles.routeDivider}>↓</div>
          <div className={styles.routePoint}>
            <div className={styles.routeTime}>
              {trip.arrival_time ? formatDate(trip.departure_date + 'T' + trip.arrival_time) : '—'}
            </div>
            <div className={styles.routeAddress}>{trip.to_address || trip.to_city}</div>
          </div>
        </div>

        <div className={styles.driver}>
          <h3>{t('trips.driver')}</h3>
          <div className={styles.driverInfo}>
            {trip.driver?.avatar_url ? (
              <img src={trip.driver.avatar_url} alt="" className={styles.driverAvatar} />
            ) : (
              <div className={styles.driverAvatarPlaceholder}>
                {driverName.charAt(0).toUpperCase()}
              </div>
            )}
            <div>
              <div 
                className={styles.driverName}
                style={{ cursor: 'pointer', textDecoration: 'underline' }}
                onClick={() => setSelectedDriverId(trip.driver_id)}
              >
                {driverName}
              </div>
              {driverRating !== undefined && (
                <div className={styles.driverRating}>
                  ★ {driverRating.toFixed(1)} ({driverReviews?.total || 0} {t('reviews.reviews')})
                </div>
              )}
            </div>
          </div>
        </div>

        {driverReviews && driverReviews.items && driverReviews.items.length > 0 && (
          <div className={styles.driverReviews}>
            <h3>{t('reviews.reviewsTitle')}</h3>
            <div className={styles.reviewsList}>
              {driverReviews.items.slice(0, 5).map((review: any) => (
                <div key={review.id} className={styles.reviewItem}>
                  <div className={styles.reviewHeader}>
                    <span className={styles.reviewAuthor}>{review.author?.name || t('reviews.anonymous')}</span>
                    <span className={styles.reviewRating}>★ {review.rating}</span>
                  </div>
                  {review.text && <p className={styles.reviewComment}>{review.text}</p>}
                  <div className={styles.reviewDate}>
                    {review.created_at ? new Date(review.created_at).toLocaleDateString('ru-RU') : ''}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Пассажиры */}
        {trip.passengers && trip.passengers.length > 0 && (
          <div className={styles.passengers}>
            <h3>Пассажиры</h3>
            <div className={styles.passengersList}>
              {trip.passengers.map((passenger: any) => (
                <div 
                  key={passenger.id} 
                  className={styles.passengerItem}
                  onClick={() => setSelectedPassengerId(passenger.id)}
                  style={{ cursor: 'pointer' }}
                >
                  {passenger.avatar_url ? (
                    <img src={passenger.avatar_url} alt="" className={styles.passengerAvatar} />
                  ) : (
                    <div className={styles.passengerAvatarPlaceholder}>
                      {passenger.name?.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div className={styles.passengerInfo}>
                    <div className={styles.passengerName}>{passenger.name}</div>
                    <div className={styles.passengerSeats}>Мест: {passenger.seats_requested}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className={styles.details}>
          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>{t('trips.availableSeats')}</span>
            <span className={styles.detailValue}>{trip.available_seats} / {trip.total_seats}</span>
          </div>
          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>{t('trips.totalSeats')}</span>
            <span className={styles.detailValue}>{trip.total_seats}</span>
          </div>
          {trip.departure_time_start && (
            <div className={styles.detailItem}>
              <span className={styles.detailLabel}>{t('trips.departureTime')}</span>
              <span className={styles.detailValue}>{trip.departure_time_start}</span>
            </div>
          )}
          {trip.arrival_time && (
            <div className={styles.detailItem}>
              <span className={styles.detailLabel}>{t('trips.arrivalTime')}</span>
              <span className={styles.detailValue}>{trip.arrival_time}</span>
            </div>
          )}
          {trip.car_model && (
            <div className={styles.detailItem}>
              <span className={styles.detailLabel}>{t('trips.car')}</span>
              <span className={styles.detailValue}>
                {trip.car_color} {trip.car_model}
              </span>
            </div>
          )}
          {trip.car_license_plate && (
            <div className={styles.detailItem}>
              <span className={styles.detailLabel}>{t('trips.licensePlate')}</span>
              <span className={styles.detailValue}>{trip.car_license_plate}</span>
            </div>
          )}
        </div>

        {(trip.luggage_allowed || trip.smoking_allowed || trip.music_allowed || trip.pets_allowed) && (
          <div className={styles.preferences}>
            <h3>{t('trips.preferences')}</h3>
            <div className={styles.preferenceItems}>
              {trip.luggage_allowed && (
                <span className={styles.preferenceBadge}>{t('trips.luggageAllowed')}</span>
              )}
              {trip.smoking_allowed && (
                <span className={styles.preferenceBadge}>{t('trips.smokingAllowed')}</span>
              )}
              {trip.music_allowed && (
                <span className={styles.preferenceBadge}>{t('trips.musicAllowed')}</span>
              )}
              {trip.pets_allowed && (
                <span className={styles.preferenceBadge}>{t('trips.petsAllowed')}</span>
              )}
            </div>
          </div>
        )}

        {trip.description && (
          <div className={styles.description}>
            <h3>{t('trips.description')}</h3>
            <p>{trip.description}</p>
          </div>
        )}

        {/* Кнопки управления для владельца */}
        {isOwner && (
          <div className={styles.ownerActions}>
            {trip.status !== 'completed' && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => navigate(`/trips/${trip.id}/edit`)}
              >
                {t('trips.edit')}
              </Button>
            )}
            {trip.status === 'draft' && (
              <Button 
                variant="primary" 
                size="sm"
                loading={publishTripMutation.isPending}
                onClick={() => publishTripMutation.mutate()}
              >
                {t('trips.publish')}
              </Button>
            )}
            {(trip.status === 'published' || trip.status === 'active') && (
              <Button 
                variant="success" 
                size="sm"
                loading={completeTripMutation.isPending}
                onClick={() => completeTripMutation.mutate()}
              >
                {t('trips.complete')}
              </Button>
            )}
            {trip.status !== 'cancelled' && trip.status !== 'completed' && (
              <Button 
                variant="danger" 
                size="sm"
                onClick={() => setIsDeleteModalOpen(true)}
              >
                {t('trips.cancel')}
              </Button>
            )}
          </div>
        )}

        {/* Кнопка бронирования для пассажиров */}
        {!isOwner && (
          <div className={styles.actions}>
            <Button 
              variant="outline" 
              size="lg" 
              onClick={() => openChatMutation.mutate()}
              loading={openChatMutation.isPending}
            >
              {t('trips.contactDriver')}
            </Button>
            {isAuthenticated ? (
              <Button variant="primary" size="lg" onClick={openBooking} disabled={maxSeats < 1}>
                {t('trips.requestToJoin')}
              </Button>
            ) : (
              <Button variant="primary" size="lg" onClick={() => navigate('/login')}>
                {t('auth.loginToBook')}
              </Button>
            )}
          </div>
        )}
      </Card>

      {/* Модальное окно бронирования */}
      <Modal
        isOpen={isBookingModalOpen}
        onClose={() => setIsBookingModalOpen(false)}
        title={t('trips.bookSeat')}
      >
        <div className={styles.bookingModal}>
          <div className={styles.bookingInfo}>
            <div>{t('trips.availableSeats')}: {trip?.available_seats ?? 0}</div>
            {maxSeats < 1 && <div>{t('errors.serverError')}</div>}
          </div>

          <div className={styles.bookingForm}>
            <Input
              label={t('requests.seatsRequested')}
              type="number"
              min={1}
              max={maxSeats}
              value={seatsRequested}
              onChange={(e) => {
                const raw = Number(e.target.value);
                const safe = Number.isFinite(raw) && raw >= 1 ? raw : 1;
                setSeatsRequested(Math.min(safe, maxSeats));
              }}
            />
            <Input
              label={t('requests.message')}
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={t('trips.contactDriver')}
            />
          </div>

          {bookingError && <div className={styles.bookingError}>{bookingError}</div>}

          <div className={styles.bookingActions}>
            <Button variant="secondary" onClick={() => setIsBookingModalOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button
              variant="primary"
              loading={createBookingMutation.isPending}
              onClick={() => createBookingMutation.mutate()}
              disabled={maxSeats < 1}
            >
              {t('trips.bookSeat')}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Модальное окно удаления поездки */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        title={t('trips.cancelTrip')}
      >
        <div className={styles.deleteModal}>
          <p>{t('trips.confirmCancelTrip')}</p>
          {deleteError && <div className={styles.bookingError}>{deleteError}</div>}
          <div className={styles.bookingActions}>
            <Button variant="secondary" onClick={() => setIsDeleteModalOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button
              variant="danger"
              loading={deleteTripMutation.isPending}
              onClick={() => deleteTripMutation.mutate()}
            >
              {t('trips.confirmCancel')}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Модальное окно профиля пассажира */}
      <Modal
        isOpen={!!selectedPassengerId}
        onClose={() => setSelectedPassengerId(null)}
        title="Профиль пассажира"
      >
        {passengerProfile ? (
          <div className={styles.passengerProfileModal}>
            <div className={styles.profileHeader}>
              {passengerProfile.avatar_url ? (
                <img src={passengerProfile.avatar_url} alt="" className={styles.profileAvatar} />
              ) : (
                <div className={styles.profileAvatarPlaceholder}>
                  {passengerProfile.name?.charAt(0).toUpperCase() || '?'}
                </div>
              )}
              <div className={styles.profileInfo}>
                <h3 className={styles.profileName}>{passengerProfile.name}</h3>
                {passengerProfile.rating_average !== undefined && (
                  <div className={styles.profileRating}>
                    ★ {passengerProfile.rating_average.toFixed(1)} ({passengerProfile.rating_count || 0} {t('reviews.reviews')})
                  </div>
                )}
              </div>
            </div>
            {passengerProfile.phone && (
              <div className={styles.profileField}>
                <span className={styles.profileLabel}>Телефон:</span>
                <span className={styles.profileValue}>{passengerProfile.phone}</span>
              </div>
            )}
            {passengerProfile.bio && (
              <div className={styles.profileField}>
                <span className={styles.profileLabel}>О себе:</span>
                <span className={styles.profileValue}>{passengerProfile.bio}</span>
              </div>
            )}
            {selectedPassengerReviews && selectedPassengerReviews.items && selectedPassengerReviews.items.length > 0 && (
              <div className={styles.driverReviews}>
                <h4 style={{ margin: '12px 0 8px' }}>{t('reviews.reviewsTitle')}</h4>
                <div className={styles.reviewsList}>
                  {selectedPassengerReviews.items.slice(0, 5).map((review: any) => (
                    <div key={review.id} className={styles.reviewItem}>
                      <div className={styles.reviewHeader}>
                        <span className={styles.reviewAuthor}>{review.author?.name || t('reviews.anonymous')}</span>
                        <span className={styles.reviewRating}>★ {review.rating}</span>
                      </div>
                      {review.text && <p className={styles.reviewComment}>{review.text}</p>}
                      <div className={styles.reviewDate}>
                        {review.created_at ? new Date(review.created_at).toLocaleDateString('ru-RU') : ''}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className={styles.profileActions}>
              {isAuthenticated && currentUser?.id !== selectedPassengerId && (
                <Button
                  variant="primary"
                  onClick={() => {
                    chatApi.createOrGetConversation(selectedPassengerId!, '').then((conv) => {
                      navigate(`/chat/${conv.id}`);
                      setSelectedPassengerId(null);
                    });
                  }}
                >
                  Написать сообщение
                </Button>
              )}
              {isAuthenticated && currentUser?.id !== selectedPassengerId && canReviewData?.can_review && (
                <Button
                  variant="primary"
                  onClick={() => {
                    openReviewModal(selectedPassengerId!, passengerProfile.name);
                    setSelectedPassengerId(null);
                  }}
                >
                  {t('reviews.leaveReview')}
                </Button>
              )}
              {isAuthenticated && currentUser?.id !== selectedPassengerId && !canReviewData?.can_review && canReviewData?.reason && (
                <div style={{ fontSize: '12px', color: '#888', marginTop: '8px' }}>
                  {canReviewData.reason}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div>Загрузка...</div>
        )}
      </Modal>

      {/* Модальное окно профиля водителя */}
      <Modal
        isOpen={!!selectedDriverId}
        onClose={() => setSelectedDriverId(null)}
        title="Профиль водителя"
      >
        {driverProfileLoading ? (
          <div>Загрузка...</div>
        ) : driverProfile ? (
          <div className={styles.passengerProfileModal}>
            <div className={styles.profileHeader}>
              {driverProfile.avatar_url ? (
                <img src={driverProfile.avatar_url} alt="" className={styles.profileAvatar} />
              ) : (
                <div className={styles.profileAvatarPlaceholder}>
                  {driverProfile.name?.charAt(0).toUpperCase() || '?'}
                </div>
              )}
              <div className={styles.profileInfo}>
                <h3 className={styles.profileName}>{driverProfile.name}</h3>
                {driverProfile.rating_average !== undefined && (
                  <div className={styles.profileRating}>
                    ★ {driverProfile.rating_average.toFixed(1)} ({driverProfile.rating_count || 0} отзывов)
                  </div>
                )}
              </div>
            </div>
            {driverProfile.phone && (
              <div className={styles.profileField}>
                <span className={styles.profileLabel}>Телефон:</span>
                <span className={styles.profileValue}>{driverProfile.phone}</span>
              </div>
            )}
            {driverProfile.bio && (
              <div className={styles.profileField}>
                <span className={styles.profileLabel}>О себе:</span>
                <span className={styles.profileValue}>{driverProfile.bio}</span>
              </div>
            )}
            {selectedDriverReviews && selectedDriverReviews.items && selectedDriverReviews.items.length > 0 && (
              <div className={styles.driverReviews}>
                <h4 style={{ margin: '12px 0 8px' }}>{t('reviews.reviewsTitle')}</h4>
                <div className={styles.reviewsList}>
                  {selectedDriverReviews.items.slice(0, 5).map((review: any) => (
                    <div key={review.id} className={styles.reviewItem}>
                      <div className={styles.reviewHeader}>
                        <span className={styles.reviewAuthor}>{review.author?.name || t('reviews.anonymous')}</span>
                        <span className={styles.reviewRating}>★ {review.rating}</span>
                      </div>
                      {review.text && <p className={styles.reviewComment}>{review.text}</p>}
                      <div className={styles.reviewDate}>
                        {review.created_at ? new Date(review.created_at).toLocaleDateString('ru-RU') : ''}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className={styles.profileActions}>
              {isAuthenticated && !isOwner && canReviewData?.can_review && (
                <Button
                  variant="primary"
                  onClick={() => {
                    openReviewModal(selectedDriverId!, driverProfile.name);
                    setSelectedDriverId(null);
                  }}
                >
                  {t('reviews.leaveReview')}
                </Button>
              )}
              {isAuthenticated && !isOwner && !canReviewData?.can_review && canReviewData?.reason && (
                <div style={{ fontSize: '12px', color: '#888', marginTop: '8px' }}>
                  {canReviewData.reason}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div>Не удалось загрузить профиль</div>
        )}
      </Modal>

      {/* Модальное окно создания отзыва */}
      <Modal
        isOpen={isReviewModalOpen}
        onClose={() => setIsReviewModalOpen(false)}
        title={t('reviews.leaveReview')}
      >
        <div className={styles.bookingModal}>
          <div className={styles.bookingForm}>
            {reviewTargetName && (
              <p style={{ marginBottom: '12px', color: '#666' }}>
                {t('reviews.reviewAbout', { name: reviewTargetName })}
              </p>
            )}
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                {t('reviews.rating')}
              </label>
              <div style={{ display: 'flex', gap: '8px' }}>
                {[1, 2, 3, 4, 5].map((star) => (
                  <span
                    key={star}
                    onClick={() => setReviewRating(star)}
                    style={{
                      fontSize: '24px',
                      cursor: 'pointer',
                      color: star <= reviewRating ? '#ffd700' : '#ccc',
                    }}
                  >
                    ★
                  </span>
                ))}
              </div>
            </div>
            <Input
              label={t('reviews.comment')}
              type="text"
              value={reviewText}
              onChange={(e) => setReviewText(e.target.value)}
              placeholder={t('reviews.commentPlaceholder')}
            />
          </div>

          {reviewError && <div className={styles.bookingError}>{reviewError}</div>}

          <div className={styles.bookingActions}>
            <Button variant="secondary" onClick={() => setIsReviewModalOpen(false)}>
              {t('reviews.cancel')}
            </Button>
            <Button
              variant="primary"
              loading={createReviewMutation.isPending}
              onClick={() => createReviewMutation.mutate()}
            >
              {t('reviews.submit')}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
