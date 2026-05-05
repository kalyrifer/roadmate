import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { DayPicker } from 'react-day-picker';
import { ru, enUS } from 'date-fns/locale';
import { format, parseISO, isValid } from 'date-fns';
import { useTranslation } from 'react-i18next';
import 'react-day-picker/style.css';
import styles from './DatePickerInput.module.css';

interface Props {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  ariaLabel?: string;
  minDate?: Date;
}

interface PopoverPos {
  top: number;
  left: number;
}

// Approximate popover footprint used for the very first render before we have
// real measurements. After mount we re-measure with getBoundingClientRect.
const POPOVER_FALLBACK_W = 320;
const POPOVER_FALLBACK_H = 360;
const VIEWPORT_GUTTER = 8;
const TRIGGER_GAP = 8;

export default function DatePickerInput({
  id,
  value,
  onChange,
  placeholder,
  className,
  ariaLabel,
  minDate,
}: Props) {
  const { i18n, t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState<PopoverPos | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  const locale = i18n.language === 'ru' ? ru : enUS;
  const selected = value && isValid(parseISO(value)) ? parseISO(value) : undefined;
  const displayFormat = i18n.language === 'ru' ? 'd MMM yyyy' : 'PP';
  const displayValue = selected ? format(selected, displayFormat, { locale }) : '';

  // Position the popover via fixed coords relative to the viewport so any
  // ancestor with overflow:hidden (e.g. HomePage hero, NewTripPage card) does
  // not clip the bottom rows of the calendar. We also flip above the trigger
  // when there is no room below.
  useLayoutEffect(() => {
    if (!open) return;
    const compute = () => {
      const trigger = triggerRef.current;
      if (!trigger) return;
      const r = trigger.getBoundingClientRect();
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      const popH = popoverRef.current?.offsetHeight || POPOVER_FALLBACK_H;
      const popW = popoverRef.current?.offsetWidth || POPOVER_FALLBACK_W;

      const spaceBelow = vh - r.bottom;
      const spaceAbove = r.top;
      const flipUp =
        spaceBelow < popH + VIEWPORT_GUTTER && spaceAbove > spaceBelow;

      let top = flipUp ? r.top - popH - TRIGGER_GAP : r.bottom + TRIGGER_GAP;
      let left = r.left;

      if (left + popW > vw - VIEWPORT_GUTTER) left = vw - popW - VIEWPORT_GUTTER;
      if (left < VIEWPORT_GUTTER) left = VIEWPORT_GUTTER;
      if (top < VIEWPORT_GUTTER) top = VIEWPORT_GUTTER;
      if (top + popH > vh - VIEWPORT_GUTTER) top = vh - popH - VIEWPORT_GUTTER;

      setPos({ top, left });
    };
    compute();
    // Re-measure once the popover has actually mounted with real dimensions.
    const raf = window.requestAnimationFrame(compute);
    window.addEventListener('resize', compute);
    window.addEventListener('scroll', compute, true);
    return () => {
      window.cancelAnimationFrame(raf);
      window.removeEventListener('resize', compute);
      window.removeEventListener('scroll', compute, true);
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      const target = e.target as Node;
      if (triggerRef.current?.contains(target)) return;
      if (popoverRef.current?.contains(target)) return;
      setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onDocClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDocClick);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  // Reset cached position when closed so the first frame after the next open
  // does not flash at stale coordinates.
  useEffect(() => {
    if (!open) setPos(null);
  }, [open]);

  const handleSelect = (day: Date | undefined) => {
    if (!day) {
      onChange('');
    } else {
      onChange(format(day, 'yyyy-MM-dd'));
      setOpen(false);
    }
  };

  return (
    <div className={`${styles.wrap} ${className ?? ''}`}>
      <button
        type="button"
        id={id}
        ref={triggerRef}
        className={styles.field}
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={ariaLabel || placeholder}
      >
        <span className={styles.icon} aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
        </span>
        <span className={displayValue ? styles.text : styles.placeholder}>
          {displayValue || placeholder || t('home.date')}
        </span>
        {displayValue && (
          <span
            role="button"
            tabIndex={0}
            className={styles.clear}
            onClick={(e) => {
              e.stopPropagation();
              handleSelect(undefined);
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                e.stopPropagation();
                handleSelect(undefined);
              }
            }}
            aria-label={t('common.clear', 'Очистить')}
          >
            ×
          </span>
        )}
      </button>

      {open &&
        createPortal(
          <div
            ref={popoverRef}
            className={styles.popover}
            role="dialog"
            style={{
              position: 'fixed',
              top: pos?.top ?? -9999,
              left: pos?.left ?? -9999,
              right: 'auto',
              bottom: 'auto',
              visibility: pos ? 'visible' : 'hidden',
            }}
          >
            <DayPicker
              mode="single"
              selected={selected}
              onSelect={handleSelect}
              locale={locale}
              weekStartsOn={1}
              disabled={minDate ? { before: minDate } : undefined}
              showOutsideDays
            />
          </div>,
          document.body,
        )}
    </div>
  );
}
