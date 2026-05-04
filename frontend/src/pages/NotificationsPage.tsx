import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button, Skeleton, Modal } from '../components/ui';
import { notificationsApi, Notification } from '../services/api/notifications';
import { requestsApi } from '../services/api/requests';
import type { TripRequest } from '../types';
import styles from './NotificationsPage.module.css';

type FilterTab = 'all' | 'unread' | 'requests' | 'trips' | 'messages';

type NotificationVisual = {
  accent: string;
  iconBadge: string;
  typeBadge: string;
  typeLabelKey: string;
  icon: JSX.Element;
};

export default function NotificationsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [activeTab, setActiveTab] = useState<FilterTab>('all');
  const [selectedRequest, setSelectedRequest] = useState<TripRequest | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Загрузка деталей заявки
  const { data: requestDetails, isLoading: isLoadingRequest } = useQuery({
    queryKey: ['request', selectedRequest?.id],
    queryFn: () =>
      selectedRequest?.id ? requestsApi.getById(selectedRequest.id) : Promise.resolve(null),
    enabled: !!selectedRequest?.id,
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['notifications', page],
    queryFn: () => notificationsApi.getAll(page, 20),
  });

  const markAsReadMutation = useMutation({
    mutationFn: (notificationId: string) => notificationsApi.markAsRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unreadCount'] });
    },
  });

  const markAllAsReadMutation = useMutation({
    mutationFn: () => notificationsApi.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unreadCount'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (notificationId: string) => notificationsApi.delete(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const confirmMutation = useMutation({
    mutationFn: (requestId: string) => requestsApi.confirm(requestId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['request'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      setIsModalOpen(false);
      setSelectedRequest(null);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ requestId, tripId }: { requestId: string; tripId: string }) =>
      requestsApi.reject(tripId, requestId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['request'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      setIsModalOpen(false);
      setSelectedRequest(null);
    },
  });

  const handleConfirmRequest = (requestId: string) => {
    confirmMutation.mutate(requestId);
  };

  const handleRejectRequest = (requestId: string, tripId: string) => {
    rejectMutation.mutate({ requestId, tripId });
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMin < 1) return t('notifications.justNow');
    if (diffMin < 60) return t('notifications.minutesAgo', { count: diffMin });
    if (diffHours < 24 && diffDays === 0) {
      return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
    }
    if (diffDays === 1) return t('chat.yesterday');
    if (diffDays < 7) return date.toLocaleDateString(undefined, { weekday: 'short' });
    return date.toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
  };

  const getNotificationVisual = (type: string): NotificationVisual => {
    const baseProps = (overrides: Partial<NotificationVisual>): NotificationVisual => ({
      accent: '',
      iconBadge: '',
      typeBadge: styles.notificationTypeBadge,
      typeLabelKey: 'notifications.types.system',
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
      ),
      ...overrides,
    });

    switch (type) {
      case 'request_new':
      case 'request_received':
        return baseProps({
          accent: styles.notificationAccent,
          iconBadge: styles.iconBadge,
          typeBadge: `${styles.notificationTypeBadge} ${styles.typeBadgePrimary}`,
          typeLabelKey: 'notifications.types.requestReceived',
          icon: (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <line x1="19" y1="8" x2="19" y2="14" />
              <line x1="22" y1="11" x2="16" y2="11" />
            </svg>
          ),
        });
      case 'request_confirmed':
        return baseProps({
          accent: `${styles.notificationAccent} ${styles.accentSuccess}`,
          iconBadge: `${styles.iconBadge} ${styles.iconBadgeSuccess}`,
          typeBadge: `${styles.notificationTypeBadge} ${styles.typeBadgeSuccess}`,
          typeLabelKey: 'notifications.types.requestConfirmed',
          icon: (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          ),
        });
      case 'request_rejected':
        return baseProps({
          accent: `${styles.notificationAccent} ${styles.accentDanger}`,
          iconBadge: `${styles.iconBadge} ${styles.iconBadgeDanger}`,
          typeBadge: `${styles.notificationTypeBadge} ${styles.typeBadgeDanger}`,
          typeLabelKey: 'notifications.types.requestRejected',
          icon: (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <circle cx="12" cy="12" r="10" />
              <line x1="15" y1="9" x2="9" y2="15" />
              <line x1="9" y1="9" x2="15" y2="15" />
            </svg>
          ),
        });
      case 'request_cancelled':
        return baseProps({
          accent: `${styles.notificationAccent} ${styles.accentNeutral}`,
          iconBadge: `${styles.iconBadge} ${styles.iconBadgeNeutral}`,
          typeLabelKey: 'notifications.types.requestCancelled',
          icon: (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 6h18" />
              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
              <path d="M10 11v6M14 11v6" />
            </svg>
          ),
        });
      case 'trip_cancelled':
        return baseProps({
          accent: `${styles.notificationAccent} ${styles.accentDanger}`,
          iconBadge: `${styles.iconBadge} ${styles.iconBadgeDanger}`,
          typeBadge: `${styles.notificationTypeBadge} ${styles.typeBadgeDanger}`,
          typeLabelKey: 'notifications.types.tripCancelled',
          icon: (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
            </svg>
          ),
        });
      case 'trip_completed':
        return baseProps({
          accent: `${styles.notificationAccent} ${styles.accentSuccess}`,
          iconBadge: `${styles.iconBadge} ${styles.iconBadgeSuccess}`,
          typeBadge: `${styles.notificationTypeBadge} ${styles.typeBadgeSuccess}`,
          typeLabelKey: 'notifications.types.tripCompleted',
          icon: (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          ),
        });
      case 'message_new':
        return baseProps({
          accent: `${styles.notificationAccent} ${styles.accentSecondary}`,
          iconBadge: `${styles.iconBadge} ${styles.iconBadgeSecondary}`,
          typeBadge: `${styles.notificationTypeBadge} ${styles.typeBadgeSecondary}`,
          typeLabelKey: 'notifications.types.messageNew',
          icon: (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          ),
        });
      case 'system':
      default:
        return baseProps({
          accent: `${styles.notificationAccent} ${styles.accentNeutral}`,
          iconBadge: `${styles.iconBadge} ${styles.iconBadgeNeutral}`,
          typeLabelKey: 'notifications.types.system',
        });
    }
  };

  const handleNotificationClick = async (notification: Notification) => {
    if (!notification.is_read) {
      try {
        await markAsReadMutation.mutateAsync(notification.id);
      } catch (err) {
        console.error('Failed to mark notification as read:', err);
      }
    }

    if (
      notification.related_request_id &&
      (notification.type === 'request_new' ||
        notification.type === 'request_confirmed' ||
        notification.type === 'request_rejected')
    ) {
      const request = {
        id: notification.related_request_id,
        trip_id: notification.related_trip_id || '',
        passenger_id: '',
        seats_requested: 0,
        status: 'pending',
        created_at: '',
      } as unknown as TripRequest;
      setSelectedRequest(request);
      setIsModalOpen(true);
    } else if (notification.related_conversation_id) {
      navigate(`/chat/${notification.related_conversation_id}`);
    } else if (notification.related_trip_id) {
      navigate(`/trips/${notification.related_trip_id}`);
    }
  };

  const handleMarkAllRead = () => {
    markAllAsReadMutation.mutate();
  };

  const handleDelete = (e: React.MouseEvent, notificationId: string) => {
    e.stopPropagation();
    deleteMutation.mutate(notificationId);
  };

  const items = data?.items ?? [];

  const tabCounts = useMemo(() => {
    const counts = { all: 0, unread: 0, requests: 0, trips: 0, messages: 0 };
    for (const n of items) {
      counts.all += 1;
      if (!n.is_read) counts.unread += 1;
      if (n.type.startsWith('request_')) counts.requests += 1;
      if (n.type.startsWith('trip_')) counts.trips += 1;
      if (n.type === 'message_new') counts.messages += 1;
    }
    return counts;
  }, [items]);

  const filteredItems = useMemo(() => {
    switch (activeTab) {
      case 'unread':
        return items.filter((n) => !n.is_read);
      case 'requests':
        return items.filter((n) => n.type.startsWith('request_'));
      case 'trips':
        return items.filter((n) => n.type.startsWith('trip_'));
      case 'messages':
        return items.filter((n) => n.type === 'message_new');
      case 'all':
      default:
        return items;
    }
  }, [items, activeTab]);

  const unreadCount = data?.stats.unread_count ?? tabCounts.unread;
  const totalCount = data?.stats.total_count ?? tabCounts.all;

  return (
    <div className={styles.page}>
      {/* Hero with gradient */}
      <section className={styles.hero}>
        <div className={styles.heroBlobs} aria-hidden>
          <div className={`${styles.heroBlob} ${styles.heroBlob1}`} />
          <div className={`${styles.heroBlob} ${styles.heroBlob2}`} />
        </div>

        <div className={styles.heroInner}>
          <div className={styles.heroCopy}>
            <span className={styles.heroEyebrow}>
              <span
                className={`${styles.heroEyebrowDot} ${
                  unreadCount === 0 ? styles.heroEyebrowDotMuted : ''
                }`}
              />
              {unreadCount > 0
                ? t('notifications.heroEyebrowUnread', { count: unreadCount })
                : t('notifications.heroEyebrowAllRead')}
            </span>
            <h1 className={styles.heroTitle}>{t('notifications.heroTitle')}</h1>
            <p className={styles.heroSubtitle}>{t('notifications.heroSubtitle')}</p>

            <div className={styles.heroStats}>
              <span className={styles.heroStatChip}>
                <span className={styles.heroStatValue}>{totalCount}</span>
                {t('notifications.statTotal')}
              </span>
              <span className={styles.heroStatChip}>
                <span className={styles.heroStatValue}>{unreadCount}</span>
                {t('notifications.statUnread')}
              </span>
            </div>
          </div>

          <div className={styles.heroActions}>
            {unreadCount > 0 && (
              <button
                type="button"
                className={styles.heroPrimaryBtn}
                onClick={handleMarkAllRead}
                disabled={markAllAsReadMutation.isPending}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                {t('notifications.markAllRead')}
              </button>
            )}
            <button
              type="button"
              className={styles.heroSecondaryBtn}
              onClick={() => navigate('/trips')}
            >
              {t('notifications.heroFindTrips')}
            </button>
          </div>
        </div>
      </section>

      {/* Filter tabs */}
      {totalCount > 0 && (
        <div className={styles.tabs} role="tablist">
          {(
            [
              { key: 'all', label: t('notifications.filterAll'), count: tabCounts.all },
              { key: 'unread', label: t('notifications.filterUnread'), count: tabCounts.unread },
              { key: 'requests', label: t('notifications.filterRequests'), count: tabCounts.requests },
              { key: 'trips', label: t('notifications.filterTrips'), count: tabCounts.trips },
              { key: 'messages', label: t('notifications.filterMessages'), count: tabCounts.messages },
            ] as const
          ).map((tab) => (
            <button
              key={tab.key}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.key}
              className={`${styles.tab} ${activeTab === tab.key ? styles.tabActive : ''}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
              {tab.count > 0 && <span className={styles.tabCount}>{tab.count}</span>}
            </button>
          ))}
        </div>
      )}

      {/* Error */}
      {error && <div className={styles.error}>{t('common.error')}</div>}

      {/* Loading skeletons */}
      {isLoading && (
        <div className={styles.list}>
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className={styles.skeletonCard}>
              <Skeleton variant="circular" width={44} height={44} />
              <div className={styles.skeletonContent}>
                <Skeleton variant="text" width="60%" height={20} />
                <Skeleton variant="text" width="80%" height={16} />
                <Skeleton variant="text" width="30%" height={14} />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty: no notifications at all */}
      {!isLoading && data && totalCount === 0 && (
        <div className={styles.empty}>
          <div className={styles.emptyIconWrap}>
            <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
          </div>
          <h3 className={styles.emptyTitle}>{t('notifications.emptyTitle')}</h3>
          <p className={styles.emptyText}>{t('notifications.emptyText')}</p>
        </div>
      )}

      {/* Empty: filter has no results */}
      {!isLoading && data && totalCount > 0 && filteredItems.length === 0 && (
        <div className={styles.empty}>
          <div className={styles.emptyIconWrap}>
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </div>
          <h3 className={styles.emptyTitle}>{t('notifications.filterEmptyTitle')}</h3>
          <p className={styles.emptyText}>{t('notifications.filterEmptyText')}</p>
        </div>
      )}

      {/* List */}
      {!isLoading && filteredItems.length > 0 && (
        <>
          <div className={styles.list}>
            {filteredItems.map((notification) => {
              const v = getNotificationVisual(notification.type);
              return (
                <article
                  key={notification.id}
                  className={`${styles.notification} ${
                    !notification.is_read ? styles.notificationUnread : ''
                  }`}
                  onClick={() => handleNotificationClick(notification)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleNotificationClick(notification);
                    }
                  }}
                >
                  <div className={v.accent} aria-hidden />
                  <div className={styles.notificationBody}>
                    <div className={v.iconBadge}>{v.icon}</div>

                    <div className={styles.notificationContent}>
                      <div className={styles.notificationHeader}>
                        <div className={styles.notificationTitleRow}>
                          {!notification.is_read && (
                            <span className={styles.unreadDot} aria-label={t('notifications.unread')} />
                          )}
                          <h3 className={styles.notificationTitle}>{notification.title}</h3>
                        </div>
                        <span className={styles.notificationTime}>
                          {formatDate(notification.created_at)}
                        </span>
                      </div>
                      <p className={styles.notificationMessage}>{notification.message}</p>
                      <div className={styles.notificationMeta}>
                        <span className={v.typeBadge}>{t(v.typeLabelKey)}</span>
                      </div>
                    </div>

                    <button
                      type="button"
                      className={styles.deleteButton}
                      onClick={(e) => handleDelete(e, notification.id)}
                      title={t('common.delete')}
                      aria-label={t('common.delete')}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      </svg>
                    </button>
                  </div>
                  <div className={styles.notificationArrow} aria-hidden>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                      <polyline points="9 18 15 12 9 6" />
                    </svg>
                  </div>
                </article>
              );
            })}
          </div>

          {data && data.total > page * 20 && (
            <div className={styles.pagination}>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
              >
                {t('common.prev')}
              </Button>
              <span className={styles.pageInfo}>
                {page} / {Math.ceil(data.total / 20)}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(page + 1)}
                disabled={page >= Math.ceil(data.total / 20)}
              >
                {t('common.next')}
              </Button>
            </div>
          )}
        </>
      )}

      {/* Модальное окно с деталями заявки */}
      <RequestDetailsModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedRequest(null);
        }}
        request={selectedRequest}
        requestDetails={requestDetails}
        isLoading={isLoadingRequest}
        onConfirm={handleConfirmRequest}
        onReject={handleRejectRequest}
        isConfirming={confirmMutation.isPending}
        isRejecting={rejectMutation.isPending}
      />
    </div>
  );
}

// Модальное окно с деталями заявки
function RequestDetailsModal({
  isOpen,
  onClose,
  request,
  requestDetails,
  isLoading,
  onConfirm,
  onReject,
  isConfirming,
  isRejecting,
}: {
  isOpen: boolean;
  onClose: () => void;
  request: TripRequest | null;
  requestDetails: TripRequest | null | undefined;
  isLoading: boolean;
  onConfirm?: (requestId: string) => void;
  onReject?: (requestId: string, tripId: string) => void;
  isConfirming?: boolean;
  isRejecting?: boolean;
}) {
  const { t } = useTranslation();

  if (!isOpen || !request) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={t('notifications.modalTitle')}>
      {isLoading ? (
        <div className={styles.modalLoading}>
          <Skeleton variant="text" width="100%" />
          <Skeleton variant="text" width="80%" />
          <Skeleton variant="text" width="60%" />
        </div>
      ) : requestDetails ? (
        <div className={styles.modalContent}>
          {/* Информация о пассажире */}
          <div className={styles.passengerCard}>
            <div className={styles.passengerAvatarLarge}>
              {requestDetails.passenger?.avatar_url ? (
                <img src={requestDetails.passenger.avatar_url} alt="" />
              ) : (
                <div className={styles.avatarPlaceholderLarge}>
                  {requestDetails.passenger?.first_name?.charAt(0)}
                  {requestDetails.passenger?.last_name?.charAt(0)}
                </div>
              )}
            </div>
            <div className={styles.passengerInfoCard}>
              <h3 className={styles.passengerNameCard}>
                {requestDetails.passenger?.first_name} {requestDetails.passenger?.last_name}
              </h3>
              {requestDetails.passenger?.rating_average !== undefined && (
                <div className={styles.ratingDisplayCard}>
                  <span className={styles.ratingStarCard}>★</span>
                  <span className={styles.ratingValueCard}>
                    {requestDetails.passenger.rating_average.toFixed(1)}
                  </span>
                  <span className={styles.ratingCountCard}>
                    ({requestDetails.passenger.rating_count} {t('notifications.reviews')})
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Детали заявки */}
          <div className={styles.requestDetailsCard}>
            <div className={styles.detailRow}>
              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>{t('notifications.seatsRequested')}</span>
                <span className={styles.detailValue}>{requestDetails.seats_requested}</span>
              </div>

              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>{t('notifications.status')}</span>
                <span
                  className={`${styles.statusBadge} ${
                    styles[`status_${requestDetails.status}` as keyof typeof styles] ?? ''
                  }`}
                >
                  {t(`notifications.statuses.${requestDetails.status}`)}
                </span>
              </div>
            </div>
          </div>

          {/* Маршрут */}
          {requestDetails.trip && (
            <div className={styles.routeCard}>
              <div className={styles.routeHeader}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                  <circle cx="12" cy="10" r="3" />
                </svg>
                <span>{t('notifications.route')}</span>
              </div>
              <div className={styles.routeDetails}>
                <div className={styles.routeCities}>
                  <span>{requestDetails.trip.from_city}</span>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                  <span>{requestDetails.trip.to_city}</span>
                </div>
                <div className={styles.routeMeta}>
                  <div className={styles.routeDate}>
                    {new Date(requestDetails.trip.departure_date).toLocaleDateString(undefined, {
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric',
                    })}
                    {requestDetails.trip.departure_time_start && (
                      <span className={styles.routeTime}>
                        {' '}
                        {t('notifications.atTime', { time: requestDetails.trip.departure_time_start })}
                      </span>
                    )}
                  </div>
                  {requestDetails.trip.available_seats !== undefined && (
                    <div className={styles.availableSeats}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                        <circle cx="9" cy="7" r="4" />
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                      </svg>
                      <span>
                        {t('notifications.availableSeats', {
                          count: requestDetails.trip.available_seats,
                        })}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Сообщение */}
          {requestDetails.message && (
            <div className={styles.messageCard}>
              <div className={styles.messageHeader}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                <span>{t('notifications.messageFromPassenger')}</span>
              </div>
              <p className={styles.messageTextCard}>{requestDetails.message}</p>
            </div>
          )}

          <div className={styles.modalActions}>
            {requestDetails.status === 'pending' && onConfirm && onReject && (
              <div className={styles.actionButtons}>
                <Button
                  variant="primary"
                  onClick={() => onConfirm(requestDetails.id)}
                  disabled={isConfirming || isRejecting}
                >
                  {isConfirming ? t('notifications.confirming') : t('notifications.accept')}
                </Button>
                <Button
                  variant="danger"
                  onClick={() => onReject(requestDetails.id, requestDetails.trip_id)}
                  disabled={isConfirming || isRejecting}
                >
                  {isRejecting ? t('notifications.rejecting') : t('notifications.reject')}
                </Button>
              </div>
            )}
            <Button variant="outline" onClick={onClose}>
              {t('common.close')}
            </Button>
          </div>
        </div>
      ) : (
        <p>{t('common.error')}</p>
      )}
    </Modal>
  );
}
