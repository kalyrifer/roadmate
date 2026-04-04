import { ReactNode, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { clsx } from 'clsx';
import styles from './Layout.module.css';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { t } = useTranslation();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className={styles.layout}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <Link to="/" className={styles.logo}>
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M16 2L2 9L16 16L30 9L16 2Z" fill="#FF6B35"/>
              <path d="M2 23L16 30L30 23V9L16 16L2 9V23Z" fill="#FF8F5C"/>
              <path d="M16 16V30" stroke="white" strokeWidth="2"/>
            </svg>
            <span>RoadMate</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className={styles.nav}>
            <Link 
              to="/trips" 
              className={clsx(styles.navLink, isActive('/trips') && styles.active)}
            >
              {t('nav.findTrips')}
            </Link>
            <Link 
              to="/trips/new" 
              className={clsx(styles.navLink, isActive('/trips/new') && styles.active)}
            >
              {t('nav.offerTrip')}
            </Link>
            <Link 
              to="/trips/my" 
              className={clsx(styles.navLink, isActive('/trips/my') && styles.active)}
            >
              {t('nav.myTrips')}
            </Link>
          </nav>

          {/* Desktop User Menu */}
          <div className={styles.userMenu}>
            <Link to="/chat" className={styles.iconButton} title={t('nav.messages')}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
            </Link>
            <Link to="/notifications" className={styles.iconButton} title={t('nav.notifications')}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
              </svg>
            </Link>
            <Link to="/profile" className={styles.avatar} title={t('nav.profile')}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </Link>
          </div>

          {/* Mobile Menu Toggle */}
          <button 
            className={styles.menuToggle}
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {mobileMenuOpen ? (
                <path d="M18 6L6 18M6 6l12 12"/>
              ) : (
                <path d="M3 12h18M3 6h18M3 18h18"/>
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <nav className={styles.mobileNav}>
            <Link 
              to="/trips" 
              className={clsx(styles.mobileNavLink, isActive('/trips') && styles.active)}
              onClick={() => setMobileMenuOpen(false)}
            >
              {t('nav.findTrips')}
            </Link>
            <Link 
              to="/trips/new" 
              className={clsx(styles.mobileNavLink, isActive('/trips/new') && styles.active)}
              onClick={() => setMobileMenuOpen(false)}
            >
              {t('nav.offerTrip')}
            </Link>
            <Link 
              to="/trips/my" 
              className={clsx(styles.mobileNavLink, isActive('/trips/my') && styles.active)}
              onClick={() => setMobileMenuOpen(false)}
            >
              {t('nav.myTrips')}
            </Link>
            <Link 
              to="/chat" 
              className={clsx(styles.mobileNavLink, isActive('/chat') && styles.active)}
              onClick={() => setMobileMenuOpen(false)}
            >
              {t('nav.messages')}
            </Link>
            <Link 
              to="/notifications" 
              className={clsx(styles.mobileNavLink, isActive('/notifications') && styles.active)}
              onClick={() => setMobileMenuOpen(false)}
            >
              {t('nav.notifications')}
            </Link>
            <Link 
              to="/profile" 
              className={clsx(styles.mobileNavLink, isActive('/profile') && styles.active)}
              onClick={() => setMobileMenuOpen(false)}
            >
              {t('nav.profile')}
            </Link>
          </nav>
        )}
      </header>

      {/* Main Content */}
      <main className={styles.main}>
        {children}
      </main>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className={styles.footerContent}>
          <p>&copy; {new Date().getFullYear()}</p>
        </div>
      </footer>
    </div>
  );
}

export default Layout;
