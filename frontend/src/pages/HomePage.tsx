import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import styles from './HomePage.module.css';

const POPULAR_ROUTES: Array<{ from: string; to: string }> = [
  { from: 'Минск', to: 'Гомель' },
  { from: 'Минск', to: 'Брест' },
  { from: 'Минск', to: 'Витебск' },
  { from: 'Минск', to: 'Гродно' },
  { from: 'Минск', to: 'Могилёв' },
  { from: 'Гомель', to: 'Брест' },
];

function HomePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [date, setDate] = useState('');

  const goToTrips = (params: { from?: string; to?: string; date?: string }) => {
    const search = new URLSearchParams();
    if (params.from) search.set('from_city', params.from);
    if (params.to) search.set('to_city', params.to);
    if (params.date) search.set('date', params.date);
    navigate(`/trips${search.toString() ? `?${search.toString()}` : ''}`);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    goToTrips({ from, to, date });
  };

  const handleSwap = () => {
    setFrom(to);
    setTo(from);
  };

  const handlePopularRoute = (route: { from: string; to: string }) => {
    setFrom(route.from);
    setTo(route.to);
    goToTrips({ from: route.from, to: route.to });
  };

  return (
    <div className={styles.page}>
      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles.heroBackground} aria-hidden="true">
          <div className={`${styles.blob} ${styles.blobOrange}`} />
          <div className={`${styles.blob} ${styles.blobBlue}`} />
        </div>

        <div className={styles.heroInner}>
          <div className={styles.eyebrow}>
            <span className={styles.eyebrowDot} />
            {t('home.eyebrow')}
          </div>

          <h1 className={styles.title}>
            {t('home.titlePart1')} <span className={styles.titleAccent}>{t('home.titleAccent')}</span>
            <br />
            {t('home.titlePart2')}
          </h1>
          <p className={styles.subtitle}>{t('home.subtitle')}</p>

          <form onSubmit={handleSearch} className={styles.searchCard}>
            <div className={styles.searchRow}>
              <div className={styles.fieldGroup}>
                <span className={`${styles.fieldDot} ${styles.fieldDotFrom}`} aria-hidden="true" />
                <div className={styles.fieldBody}>
                  <label htmlFor="home-from" className={styles.fieldLabel}>{t('home.from')}</label>
                  <input
                    id="home-from"
                    type="text"
                    placeholder={t('home.fromPlaceholder')}
                    value={from}
                    onChange={(e) => setFrom(e.target.value)}
                    className={styles.fieldInput}
                    autoComplete="off"
                  />
                </div>
              </div>

              <button
                type="button"
                onClick={handleSwap}
                className={styles.swapButton}
                aria-label={t('home.swap')}
                title={t('home.swap')}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="17 1 21 5 17 9" />
                  <path d="M3 11V9a4 4 0 0 1 4-4h14" />
                  <polyline points="7 23 3 19 7 15" />
                  <path d="M21 13v2a4 4 0 0 1-4 4H3" />
                </svg>
              </button>

              <div className={styles.fieldGroup}>
                <span className={`${styles.fieldDot} ${styles.fieldDotTo}`} aria-hidden="true" />
                <div className={styles.fieldBody}>
                  <label htmlFor="home-to" className={styles.fieldLabel}>{t('home.to')}</label>
                  <input
                    id="home-to"
                    type="text"
                    placeholder={t('home.toPlaceholder')}
                    value={to}
                    onChange={(e) => setTo(e.target.value)}
                    className={styles.fieldInput}
                    autoComplete="off"
                  />
                </div>
              </div>

              <div className={`${styles.fieldGroup} ${styles.fieldGroupDate}`}>
                <span className={styles.fieldIcon} aria-hidden="true">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                    <line x1="16" y1="2" x2="16" y2="6" />
                    <line x1="8" y1="2" x2="8" y2="6" />
                    <line x1="3" y1="10" x2="21" y2="10" />
                  </svg>
                </span>
                <div className={styles.fieldBody}>
                  <label htmlFor="home-date" className={styles.fieldLabel}>{t('home.date')}</label>
                  <input
                    id="home-date"
                    type="date"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    className={styles.fieldInput}
                  />
                </div>
              </div>

              <button type="submit" className={styles.searchSubmit}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="7" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
                <span>{t('home.search')}</span>
              </button>
            </div>
          </form>

          <div className={styles.popularRow}>
            <span className={styles.popularLabel}>{t('home.popularRoutes')}:</span>
            <div className={styles.popularChips}>
              {POPULAR_ROUTES.map((r) => (
                <button
                  type="button"
                  key={`${r.from}-${r.to}`}
                  onClick={() => handlePopularRoute(r)}
                  className={styles.popularChip}
                >
                  {r.from}
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                  {r.to}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Stats strip */}
      <section className={styles.stats}>
        <div className={styles.statItem}>
          <div className={styles.statValue}>10k+</div>
          <div className={styles.statLabel}>{t('home.stat1')}</div>
        </div>
        <div className={styles.statDivider} aria-hidden="true" />
        <div className={styles.statItem}>
          <div className={styles.statValue}>50+</div>
          <div className={styles.statLabel}>{t('home.stat2')}</div>
        </div>
        <div className={styles.statDivider} aria-hidden="true" />
        <div className={styles.statItem}>
          <div className={styles.statValue}>4.8★</div>
          <div className={styles.statLabel}>{t('home.stat3')}</div>
        </div>
        <div className={styles.statDivider} aria-hidden="true" />
        <div className={styles.statItem}>
          <div className={styles.statValue}>24/7</div>
          <div className={styles.statLabel}>{t('home.stat4')}</div>
        </div>
      </section>

      {/* How it works */}
      <section className={styles.section}>
        <header className={styles.sectionHeader}>
          <span className={styles.sectionEyebrow}>{t('home.howItWorks')}</span>
          <h2 className={styles.sectionTitle}>{t('home.howItWorksTitle')}</h2>
        </header>

        <div className={styles.steps}>
          <div className={styles.stepCard}>
            <div className={styles.stepNumber}>1</div>
            <div className={styles.stepIcon} aria-hidden="true">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </div>
            <h3 className={styles.stepTitle}>{t('home.step1Title')}</h3>
            <p className={styles.stepText}>{t('home.step1Desc')}</p>
          </div>
          <div className={styles.stepConnector} aria-hidden="true" />
          <div className={styles.stepCard}>
            <div className={styles.stepNumber}>2</div>
            <div className={styles.stepIcon} aria-hidden="true">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <h3 className={styles.stepTitle}>{t('home.step2Title')}</h3>
            <p className={styles.stepText}>{t('home.step2Desc')}</p>
          </div>
          <div className={styles.stepConnector} aria-hidden="true" />
          <div className={styles.stepCard}>
            <div className={styles.stepNumber}>3</div>
            <div className={styles.stepIcon} aria-hidden="true">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 11l18-8-8 18-2-7-8-3z" />
              </svg>
            </div>
            <h3 className={styles.stepTitle}>{t('home.step3Title')}</h3>
            <p className={styles.stepText}>{t('home.step3Desc')}</p>
          </div>
        </div>
      </section>

      {/* Why RoadMate */}
      <section className={styles.section}>
        <header className={styles.sectionHeader}>
          <span className={styles.sectionEyebrow}>{t('home.whyEyebrow')}</span>
          <h2 className={styles.sectionTitle}>{t('home.whyTitle')}</h2>
        </header>

        <div className={styles.featureGrid}>
          <div className={styles.featureCard}>
            <div className={`${styles.featureIcon} ${styles.featureIconOrange}`} aria-hidden="true">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s-8-4.5-8-11.8A8 8 0 0 1 12 2a8 8 0 0 1 8 8.2c0 7.3-8 11.8-8 11.8z" />
                <circle cx="12" cy="10" r="3" />
              </svg>
            </div>
            <h3 className={styles.featureTitle}>{t('home.feature1Title')}</h3>
            <p className={styles.featureText}>{t('home.feature1Desc')}</p>
          </div>
          <div className={styles.featureCard}>
            <div className={`${styles.featureIcon} ${styles.featureIconBlue}`} aria-hidden="true">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="M9 12l2 2 4-4" />
              </svg>
            </div>
            <h3 className={styles.featureTitle}>{t('home.feature2Title')}</h3>
            <p className={styles.featureText}>{t('home.feature2Desc')}</p>
          </div>
          <div className={styles.featureCard}>
            <div className={`${styles.featureIcon} ${styles.featureIconGreen}`} aria-hidden="true">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            </div>
            <h3 className={styles.featureTitle}>{t('home.feature3Title')}</h3>
            <p className={styles.featureText}>{t('home.feature3Desc')}</p>
          </div>
          <div className={styles.featureCard}>
            <div className={`${styles.featureIcon} ${styles.featureIconPurple}`} aria-hidden="true">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="1" x2="12" y2="23" />
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
            </div>
            <h3 className={styles.featureTitle}>{t('home.feature4Title')}</h3>
            <p className={styles.featureText}>{t('home.feature4Desc')}</p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className={styles.cta}>
        <div className={styles.ctaInner}>
          <div className={styles.ctaCopy}>
            <span className={styles.ctaEyebrow}>{t('home.ctaEyebrow')}</span>
            <h2 className={styles.ctaTitle}>{t('home.ctaTitle')}</h2>
            <p className={styles.ctaText}>{t('home.ctaDesc')}</p>
          </div>
          <div className={styles.ctaActions}>
            <button
              type="button"
              className={styles.ctaPrimary}
              onClick={() => navigate('/trips/new')}
            >
              {t('home.offerRide')}
            </button>
            <button
              type="button"
              className={styles.ctaSecondary}
              onClick={() => navigate('/trips')}
            >
              {t('home.findRide')}
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

export default HomePage;
