/**
 * DetailsEditor — Details card content for the Setup hub (§4.1, §11).
 *
 * v50b-3 redesign: no internal Save button. The card's "Save & confirm"
 * footer button drives persistence. Parent passes its own draft state
 * via `form` + `onChange`, so it can call `onSaveAndConfirm` without
 * needing an imperative API on this component.
 *
 * Empty date fields are normalised to `null` when saved (backend rejects
 * empty strings — v50b-3 bug fix).
 *
 * Props:
 *   - form          — controlled form state { name, description, location, timezone, start_date, end_date }
 *   - onChange(next) — callback when any field changes
 *   - isAdmin       — read-only if false
 *   - error         — error string from the parent (shown at top of form)
 */

import { useI18n } from '../hooks/useI18n';
import { formatErrorMessage } from '../services/api';
import TimezonePicker from './TimezonePicker';

// v0.70d-2b (R13): `COMMON_TIMEZONES` previously lived here as a
// hand-curated 12-zone list. It moved into the new `TimezonePicker`
// component (as a fallback for browsers without
// `Intl.supportedValuesOf`) so Moimio has one source of truth for
// the picker across DetailsEditor and UserPreferencesPanel.

const inputClass =
  'w-full rounded-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-steel-blue ' +
  'bg-white dark:bg-white/5 border border-card ' +
  'text-body';

/**
 * Build a patch from a form object ready for the backend.
 * Empty strings in date fields become null.
 */
export function detailsFormToPatch(form) {
  return {
    name: form.name,
    description: form.description || null,
    location: form.location || null,
    timezone: form.timezone || 'UTC',
    start_date: form.start_date || null,
    end_date: form.end_date || null,
  };
}

export default function DetailsEditor({ form, onChange, isAdmin, error }) {
  const { t } = useI18n();

  if (!isAdmin) {
    return (
      <p className="text-sm" style={{ color: 'var(--text-subtle)' }}>
        {t('common.no_access')}
      </p>
    );
  }

  const set = (k, v) => onChange({ ...form, [k]: v });

  return (
    <div className="space-y-3">
      <div>
        <label className="block text-xs font-semibold mb-1" style={{ color: 'var(--text-muted)' }}>
          {t('event.details.name')} *
        </label>
        <input
          type="text"
          value={form.name || ''}
          required
          onChange={e => set('name', e.target.value)}
          className={inputClass}
        />
      </div>

      <div>
        <label className="block text-xs font-semibold mb-1" style={{ color: 'var(--text-muted)' }}>
          {t('event.details.description')}
        </label>
        <textarea
          value={form.description || ''}
          rows={3}
          onChange={e => set('description', e.target.value)}
          className={`${inputClass} resize-none`}
        />
      </div>

      <div>
        <label className="block text-xs font-semibold mb-1" style={{ color: 'var(--text-muted)' }}>
          {t('event.details.location')}
        </label>
        <input
          type="text"
          value={form.location || ''}
          onChange={e => set('location', e.target.value)}
          className={inputClass}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-semibold mb-1" style={{ color: 'var(--text-muted)' }}>
            {t('event.details.start')}
          </label>
          <input
            type="date"
            value={form.start_date || ''}
            onChange={e => set('start_date', e.target.value)}
            className={inputClass}
          />
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1" style={{ color: 'var(--text-muted)' }}>
            {t('event.details.end')}
          </label>
          <input
            type="date"
            value={form.end_date || ''}
            onChange={e => set('end_date', e.target.value)}
            className={inputClass}
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-semibold mb-1" style={{ color: 'var(--text-muted)' }}>
          {t('prefs.timezone')}
        </label>
        {/* v0.70d-2b (R13): TimezonePicker replaces the hand-rolled
            12-zone <select>. Now accepts any IANA zone via datalist
            autocomplete over `Intl.supportedValuesOf('timeZone')`. */}
        <TimezonePicker
          value={form.timezone || 'UTC'}
          onChange={v => set('timezone', v)}
          className={inputClass}
          ariaLabel={t('prefs.timezone')}
        />
      </div>

      <p className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>
        {t('event.details.date_hint')}
      </p>

      {error && (() => {
        const { primary, detail } = formatErrorMessage(error, t);
        return (
          <div className="bg-alert-tint text-alert text-xs rounded-card p-2">
            <p className="font-semibold">{primary}</p>
            {detail && <p className="text-xs opacity-70 mt-1">{detail}</p>}
          </div>
        );
      })()}
    </div>
  );
}
