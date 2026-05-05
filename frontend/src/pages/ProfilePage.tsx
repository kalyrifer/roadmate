import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { usersApi } from '../services/api';
import { useAuthStore } from '../stores/auth';
import type { UserProfile } from '../types';
import styles from './ProfilePage.module.css';

export default function ProfilePage() {
  const { t, i18n } = useTranslation();
  const { logout } = useAuthStore();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    bio: '',
    language: 'ru',
  });
  const [successMessage, setSuccessMessage] = useState('');
  const [updateError, setUpdateError] = useState('');

  // Загрузка профиля
  const { data: profile, isLoading, error } = useQuery<UserProfile>({
    queryKey: ['myProfile'],
    queryFn: () => usersApi.getMyProfile(),
  });

  // Обновление профиля
  const updateMutation = useMutation({
    mutationFn: (data: { name?: string; phone?: string; bio?: string; language?: string }) =>
      usersApi.updateMyProfile(data),
    onSuccess: (updatedProfile) => {
      setIsEditing(false);
      setSuccessMessage(t('profile.updateSuccess'));
      const lang = ((updatedProfile as unknown) as { language?: string }).language || 'ru';
      setFormData({
        name: updatedProfile.name || '',
        phone: updatedProfile.phone || '',
        bio: updatedProfile.bio || '',
        language: lang,
      });
      queryClient.invalidateQueries({ queryKey: ['myProfile'] });
      setTimeout(() => setSuccessMessage(''), 3000);
    },
    onError: (err: unknown) => {
      let message: string | undefined;
      if (typeof err === 'string') {
        message = err;
      } else if (err && typeof err === 'object') {
        const anyErr = err as { message?: string; response?: { data?: { detail?: string } } };
        message = anyErr.response?.data?.detail || anyErr.message;
      }
      setSuccessMessage('');
      setUpdateError(message || t('profile.updateError'));
      setTimeout(() => setUpdateError(''), 4000);
    },
  });

  useEffect(() => {
    if (profile) {
      const lang = ((profile as unknown) as { language?: string }).language || 'ru';
      setFormData({
        name: profile.name || '',
        phone: profile.phone || '',
        bio: profile.bio || '',
        language: lang,
      });
    }
  }, [profile]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(formData);
    if (formData.language && formData.language !== i18n.language) {
      i18n.changeLanguage(formData.language);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleLogout = async () => {
    await queryClient.clear();
    await logout();
  };

  if (isLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.section}>
          <div className={styles.loading}>{t('common.loading')}</div>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className={styles.page}>
        <div className={styles.section}>
          <div className={styles.error}>{t('profile.loadError')}</div>
        </div>
      </div>
    );
  }

  const memberSinceLocale = i18n.language === 'en' ? 'en-US' : 'ru-RU';
  const memberSince = new Date(profile.created_at).toLocaleDateString(memberSinceLocale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const initials =
    (profile.name || profile.email || '?')
      .split(/[\s@]+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((s) => s.charAt(0).toUpperCase())
      .join('') || '?';

  return (
    <div className={styles.page}>
      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles.heroBlobs} aria-hidden>
          <div className={`${styles.heroBlob} ${styles.heroBlob1}`} />
          <div className={`${styles.heroBlob} ${styles.heroBlob2}`} />
        </div>

        <div className={styles.heroInner}>
          <div className={styles.avatarWrap}>
            <div className={styles.avatar}>
              {profile.avatar_url ? (
                <img
                  src={profile.avatar_url}
                  alt={profile.name || profile.email}
                  className={styles.avatarImage}
                />
              ) : (
                <div
                  className={styles.avatarPlaceholder}
                  style={{ fontSize: '2rem', fontWeight: 700 }}
                >
                  {initials}
                </div>
              )}
            </div>
            {profile.rating_count > 0 && (
              <span className={styles.avatarBadge}>
                <span className={styles.avatarBadgeStar}>★</span>
                {profile.rating_average.toFixed(1)}
              </span>
            )}
          </div>

          <div className={styles.heroCopy}>
            <span className={styles.heroEyebrow}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                <line x1="16" y1="2" x2="16" y2="6" />
                <line x1="8" y1="2" x2="8" y2="6" />
                <line x1="3" y1="10" x2="21" y2="10" />
              </svg>
              {t('profile.memberSince')} {memberSince}
            </span>
            <h1 className={styles.heroName}>{profile.name || profile.email}</h1>
            <p className={styles.heroEmail}>{profile.email}</p>

            <div className={styles.heroStats}>
              <span className={styles.heroStatChip}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                </svg>
                <span className={styles.heroStatValue}>
                  {(profile.rating_average ?? 0).toFixed(1)}
                </span>
                {t('profile.rating')}
              </span>
              <span className={styles.heroStatChip}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                <span className={styles.heroStatValue}>{profile.rating_count ?? 0}</span>
                {t('profile.reviews')}
              </span>
              <span className={styles.heroStatChip}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M3 12h18M3 6h18M3 18h18" />
                </svg>
                <span className={styles.heroStatValue}>{profile.trips_count ?? 0}</span>
                {t('profile.trips')}
              </span>
            </div>
          </div>

          <div className={styles.heroActions}>
            <button
              type="button"
              className={styles.heroPrimaryBtn}
              onClick={() => setIsEditing((prev) => !prev)}
            >
              {isEditing ? (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                  {t('common.cancel')}
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                  </svg>
                  {t('profile.edit')}
                </>
              )}
            </button>
            <button
              type="button"
              className={styles.heroSecondaryBtn}
              onClick={handleLogout}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
              {t('profile.logout')}
            </button>
          </div>
        </div>
      </section>

      {/* Success message */}
      {successMessage && (
        <div className={styles.successMessage}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
          {successMessage}
        </div>
      )}

      {/* Error message */}
      {updateError && (
        <div className={styles.error}>
          {updateError}
        </div>
      )}

      {/* Edit form OR About */}
      {isEditing ? (
        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>{t('profile.editProfile')}</h2>
          </div>
          <form onSubmit={handleSubmit} className={styles.form}>
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label className={styles.formLabel} htmlFor="profile-name">
                  {t('profile.name')}
                </label>
                <input
                  id="profile-name"
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  className={styles.formInput}
                  placeholder={t('profile.namePlaceholder')}
                />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.formLabel} htmlFor="profile-phone">
                  {t('profile.phone')}
                </label>
                <input
                  id="profile-phone"
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
              <label className={styles.formLabel} htmlFor="profile-bio">
                {t('profile.bio')}
              </label>
              <textarea
                id="profile-bio"
                name="bio"
                value={formData.bio}
                onChange={handleChange}
                className={styles.formTextarea}
                placeholder={t('profile.bioPlaceholder')}
                rows={4}
              />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.formLabel} htmlFor="profile-language">
                {t('profile.language')}
              </label>
              <select
                id="profile-language"
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
              <button
                type="button"
                className={styles.cancelButton}
                onClick={() => setIsEditing(false)}
              >
                {t('common.cancel')}
              </button>
              <button
                type="submit"
                className={styles.submitButton}
                disabled={updateMutation.isPending}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                {updateMutation.isPending ? t('common.loading') : t('profile.save')}
              </button>
            </div>
          </form>
        </section>
      ) : (
        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>{t('profile.about')}</h2>
            <button
              type="button"
              className={styles.sectionAction}
              onClick={() => setIsEditing(true)}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
              {t('profile.edit')}
            </button>
          </div>

          <div className={styles.infoGrid}>
            <div className={styles.infoItem}>
              <div className={styles.infoIcon}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                  <polyline points="22,6 12,13 2,6" />
                </svg>
              </div>
              <div className={styles.infoContent}>
                <span className={styles.infoLabel}>{t('profile.email')}</span>
                <span className={styles.infoValue}>{profile.email}</span>
              </div>
            </div>

            <div className={`${styles.infoItem}`}>
              <div className={`${styles.infoIcon} ${styles.infoIconSecondary}`}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
                </svg>
              </div>
              <div className={styles.infoContent}>
                <span className={styles.infoLabel}>{t('profile.phone')}</span>
                <span className={styles.infoValue}>
                  {profile.phone || <em style={{ color: 'var(--gray-500)' }}>—</em>}
                </span>
              </div>
            </div>
          </div>

          {profile.bio ? (
            <p className={styles.bio}>{profile.bio}</p>
          ) : (
            <p className={styles.bioEmpty}>{t('profile.bioPlaceholder')}…</p>
          )}
        </section>
      )}

      {/* Reviews */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>{t('profile.reviewsTitle')}</h2>
        </div>

        {profile.reviews && profile.reviews.length > 0 ? (
          <div className={styles.reviewsList}>
            {profile.reviews.map((review) => (
              <article key={review.id} className={styles.reviewCard}>
                <div className={styles.reviewHeader}>
                  <div className={styles.reviewAuthorBlock}>
                    {review.author?.avatar_url ? (
                      <img
                        src={review.author.avatar_url}
                        alt=""
                        className={styles.reviewAuthorAvatar}
                      />
                    ) : (
                      <div className={styles.reviewAuthorAvatarPlaceholder}>
                        {(review.author?.name || t('reviews.anonymous')).charAt(0).toUpperCase()}
                      </div>
                    )}
                    <span className={styles.reviewAuthorName}>
                      {review.author?.name || t('reviews.anonymous')}
                    </span>
                  </div>
                  <span className={styles.reviewDate}>
                    {new Date(review.created_at).toLocaleDateString(memberSinceLocale, {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                    })}
                  </span>
                </div>
                <div className={styles.reviewRating}>
                  {[1, 2, 3, 4, 5].map((star) => (
                    <span
                      key={star}
                      className={star <= review.rating ? styles.star : styles.starEmpty}
                    >
                      ★
                    </span>
                  ))}
                </div>
                {review.text && <p className={styles.reviewText}>{review.text}</p>}
              </article>
            ))}
          </div>
        ) : (
          <div className={styles.emptyReviews}>
            <div className={styles.emptyReviewsIcon}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
            </div>
            <p>{t('profile.noReviews')}</p>
          </div>
        )}
      </section>
    </div>
  );
}
