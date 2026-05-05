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
  const wrapRef = useRef<HTMLDivElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const [popoverPos, setPopoverPos] = useState<{ top: number; left: number; width: number } | null>(null);

  const locale = i18n.language === 'ru' ? ru : enUS;
  const selected = value && isValid(parseISO(value)) ? parseISO(value) : undefined;
  const displayFormat = i18n.language === 'ru' ? 'd MMM yyyy' : 'PP';
  const displayValue = selected ? format(selected, displayFormat, { locale }) : '';

  // Position the portalled popover relative to the trigger button.
  // Recomputes on open + on scroll/resize so the calendar tracks the
  // input even when it's near the bottom of the viewport.
  useLayoutEffect(() => {
    if (!open) return;
    const updatePosition = () => {
      const trigger = wrapRef.current;
      if (!trigger) return;
      const rect = trigger.getBoundingClientRect();
      const popover = popoverRef.current;
      const popoverHeight = popover?.offsetHeight ?? 360;
      const popoverWidth = popover?.offsetWidth ?? rect.width;
      const margin = 8;
      const viewportH = window.innerHeight;
      const viewportW = window.innerWidth;

      // Prefer below; flip above if there's not enough room below
      // and there's more room above.
      const spaceBelow = viewportH - rect.bottom;
      const spaceAbove = rect.top;
      let top = rect.bottom + margin;
      if (spaceBelow < popoverHeight + margin && spaceAbove > spaceBelow) {
        top = Math.max(margin, rect.top - popoverHeight - margin);
      } else {
        // Clamp so it stays on screen even if it doesn't fit perfectly.
        top = Math.min(top, viewportH - popoverHeight - margin);
        top = Math.max(margin, top);
      }

      let left = rect.left;
      if (left + popoverWidth > viewportW - margin) {
        left = Math.max(margin, viewportW - popoverWidth - margin);
      }

      setPopoverPos({ top, left, width: rect.width });
    };

    updatePosition();
    window.addEventListener('resize', updatePosition);
    window.addEventListener('scroll', updatePosition, true);
    return () => {
      window.removeEventListener('resize', updatePosition);
      window.removeEventListener('scroll', updatePosition, true);
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      const target = e.target as Node;
      if (wrapRef.current?.contains(target)) return;
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

  const handleSelect = (day: Date | undefined) => {
    if (!day) {
      onChange('');
    } else {
      onChange(format(day, 'yyyy-MM-dd'));
      setOpen(false);
    }
  };

  return (
    <div className={`${styles.wrap} ${className ?? ''}`} ref={wrapRef}>
      <button
        type="button"
        id={id}
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
            style={
              popoverPos
                ? {
                    position: 'fixed',
                    top: popoverPos.top,
                    left: popoverPos.left,
                    minWidth: popoverPos.width,
                  }
                : { position: 'fixed', visibility: 'hidden' }
            }
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
          document.body
        )}
    </div>
  );
}
