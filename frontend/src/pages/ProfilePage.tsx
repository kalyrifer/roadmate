import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Button, Input, Card } from '../components/ui';
import { usersApi, getAccessToken } from '../services/api';
import { useAuthStore } from '../stores/auth';
import type { UserProfile } from '../types';
import styles from './ProfilePage.module.css';

export default function ProfilePage() {
  const { t } = useTranslation();
  const { logout } = useAuthStore();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    bio: '',
    language: 'ru',
  });
  const [successMessage, setSuccessMessage] = useState('');

  // Debug: Log token state on mount
  useEffect(() => {
    const token = getAccessToken();
    console.log('[ProfilePage] Token on mount:', token ? 'present' : 'missing');
  }, []);

  // Загрузка профиля
  const { data: profile, isLoading, error, refetch } = useQuery<UserProfile>({
    queryKey: ['myProfile'],
    queryFn: async () => {
      const token = getAccessToken();
      console.log('[ProfilePage] QueryFn - Token before API call:', token ? 'present' : 'missing');
      try {
        const result = await usersApi.getMyProfile();
        console.log('[ProfilePage] QueryFn - API success:', result);
        return result;
      } catch (err: any) {
        console.log('[ProfilePage] QueryFn - API error:', err.response?.status, err.response?.data);
        throw err;
      }
    },
  });

  // Обновление профиля
  const updateMutation = useMutation({
    mutationFn: (data: { name?: string; phone?: string; bio?: string; language?: string }) =>
      usersApi.updateMyProfile(data),
    onSuccess: (updatedProfile) => {
      setIsEditing(false);
      setSuccessMessage(t('profile.updateSuccess'));
      setFormData({
        name: updatedProfile.name || '',
        phone: updatedProfile.phone || '',
        bio: updatedProfile.bio || '',
        language: (updatedProfile as any).language || 'ru',
      });
      setTimeout(() => setSuccessMessage(''), 3000);
    },
  });

  // Инициализация формы при загрузке профиля
  useEffect(() => {
    if (profile) {
      setFormData({
        name: profile.name || '',
        phone: profile.phone || '',
        bio: profile.bio || '',
        language: (profile as any).language || 'ru',
      });
    }
  }, [profile]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  if (isLoading) {
    return (
      <div className={styles.container}>
        <Card className={styles.profileCard}>
          <div className={styles.loading}>{t('common.loading')}</div>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <Card className={styles.profileCard}>
          <div className={styles.error}>{t('profile.loadError')}</div>
        </Card>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className={styles.container}>
        <Card className={styles.profileCard}>
          <div className={styles.error}>{t('profile.notFound')}</div>
        </Card>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.profileCard}>
        {/* Cover gradient */}
        <div className={styles.cover}></div>

        <div className={styles.profileContent}>
          {successMessage && (
            <div className={styles.successMessage}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
              {successMessage}
            </div>
          )}

          {/* Header with avatar */}
          <div className={styles.header}>
            <div className={styles.avatar}>
              {profile.avatar_url ? (
                <img src={profile.avatar_url} alt={profile.name} className={styles.avatarImage} />
              ) : (
                <div className={styles.avatarPlaceholder}>
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                </div>
              )}
            </div>
            <div className={styles.headerInfo}>
              <h1 className={styles.name}>{profile.name || profile.email}</h1>
              <p className={styles.email}>{profile.email}</p>
            </div>
            <div className={styles.actions}>
              <button className={styles.editButton} onClick={() => setIsEditing(!isEditing)}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
                {isEditing ? t('common.cancel') : t('profile.edit')}
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className={styles.stats}>
            <div className={styles.statItem}>
              <span className={styles.statValue}>{profile.rating_average?.toFixed(1) || '0.0'}</span>
              <span className={styles.statLabel}>{t('profile.rating')}</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statValue}>{profile.rating_count || 0}</span>
              <span className={styles.statLabel}>{t('profile.reviews')}</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statValue}>{profile.trips_count || 0}</span>
              <span className={styles.statLabel}>{t('profile.trips')}</span>
            </div>
          </div>

          {/* View Mode - Info */}
          {!isEditing && (
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>{t('profile.about')}</h3>
              <div className={styles.infoGrid}>
                {profile.phone && (
                  <div className={styles.infoItem}>
                    <div className={styles.infoIcon}>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
                      </svg>
                    </div>
                    <div className={styles.infoContent}>
                      <span className={styles.infoLabel}>{t('profile.phone')}</span>
                      <span className={styles.infoValue}>{profile.phone}</span>
                    </div>
                  </div>
                )}
                <div className={styles.infoItem}>
                  <div className={styles.infoIcon}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                      <line x1="16" y1="2" x2="16" y2="6" />
                      <line x1="8" y1="2" x2="8" y2="6" />
                      <line x1="3" y1="10" x2="21" y2="10" />
                    </svg>
                  </div>
                  <div className={styles.infoContent}>
                    <span className={styles.infoLabel}>{t('profile.memberSince')}</span>
                    <span className={styles.infoValue}>
                      {new Date(profile.created_at).toLocaleDateString('ru-RU', { 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric' 
                      })}
                    </span>
                  </div>
                </div>
              </div>
              {profile.bio && (
                <div className={styles.bio}>
                  {profile.bio}
                </div>
              )}
            </div>
          )}

          {/* Edit Mode - Form */}
          {isEditing && (
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>{t('profile.editProfile')}</h3>
              <form onSubmit={handleSubmit} className={styles.form}>
                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>{t('profile.name')}</label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      className={styles.formInput}
                      placeholder={t('profile.namePlaceholder')}
                    />
                  </div>
                  <div className={styles.formGroup}>
                    <label className={styles.formLabel}>{t('profile.phone')}</label>
                    <input
                      type="tel"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      className={styles.formInput}
                      placeholder={t('profile.phonePlaceholder')}
                    />
                  </div>
                </div>
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>{t('profile.bio')}</label>
                  <textarea
                    name="bio"
                    value={formData.bio}
                    onChange={handleChange}
                    className={styles.formTextarea}
                    placeholder={t('profile.bioPlaceholder')}
                    rows={4}
                  />
                </div>
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>{t('profile.language')}</label>
                  <select
                    name="language"
                    value={formData.language}
                    onChange={handleChange}
                    className={styles.formSelect}
                  >
                    <option value="ru">Русский</option>
                    <option value="en">English</option>
                  </select>
                </div>
                <div className={styles.formActions}>
                  <button type="submit" className={styles.submitButton} disabled={updateMutation.isPending}>
                    {updateMutation.isPending ? t('common.loading') : t('profile.save')}
                  </button>
                  <button type="button" className={styles.cancelButton} onClick={() => setIsEditing(false)}>
                    {t('common.cancel')}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Reviews */}
          {profile.reviews && profile.reviews.length > 0 && (
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>{t('profile.reviewsTitle')}</h3>
              <div className={styles.reviews}>
                {profile.reviews.map((review) => (
                  <div key={review.id} className={styles.reviewCard}>
                    <div className={styles.reviewHeader}>
                      <div className={styles.reviewRating}>
                        {[1, 2, 3, 4, 5].map((star) => (
                          <span key={star} className={star <= review.rating ? styles.star : styles.starEmpty}>
                            ★
                          </span>
                        ))}
                      </div>
                      <span className={styles.reviewDate}>
                        {new Date(review.created_at).toLocaleDateString('ru-RU', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                        })}
                      </span>
                    </div>
                    {review.text && <p className={styles.reviewText}>{review.text}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {(!profile.reviews || profile.reviews.length === 0) && (
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>{t('profile.reviewsTitle')}</h3>
              <div className={styles.emptyReviews}>
                {t('profile.noReviews')}
              </div>
            </div>
          )}

          {/* Logout button at bottom right */}
          <div className={styles.logoutContainer}>
            <button className={styles.logoutButton} onClick={() => logout()}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
              {t('profile.logout')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}