/**
 * CopyFromEventPicker — the single shared control for "reuse settings from a
 * previous event". Used in two places so they can never drift apart:
 *   - the Create-event form (source dropdown shown, user picks an event)
 *   - the Duplicate overlay (source fixed to the clicked event, dropdown hidden)
 *
 * It edits a CopyOptions object — { marks, registration_form, custom_fields,
 * group_types, staff } — matching the backend schema exactly. GDPR-safe: only
 * configuration is ever copied, never participants.
 *
 * Props:
 *   events           [{ id, name }]  source options (only when showSourceSelect)
 *   sourceId         string          selected source event id ('' = none)
 *   onSourceChange   (id) => void
 *   options          CopyOptions
 *   onOptionsChange  (next) => void
 *   showSourceSelect boolean         default true; false when source is fixed
 */
import { useI18n } from '../hooks/useI18n';

// Display order of the five copyable groups.
export const COPY_GROUPS = ['marks', 'registration_form', 'custom_fields', 'group_types', 'staff'];

export const DEFAULT_COPY_OPTIONS = {
  marks: true,
  registration_form: true,
  custom_fields: true,
  group_types: true,
  staff: true,
};

export default function CopyFromEventPicker({
  events = [],
  sourceId = '',
  onSourceChange,
  options,
  onOptionsChange,
  showSourceSelect = true,
}) {
  const { t } = useI18n();
  const opts = options || DEFAULT_COPY_OPTIONS;
  const toggle = (key) => onOptionsChange({ ...opts, [key]: !opts[key] });

  const selectCls =
    'w-full rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]';

  return (
    <div className="space-y-3">
      {showSourceSelect && (
        <select value={sourceId} onChange={(e) => onSourceChange?.(e.target.value)} className={selectCls}>
          <option value="">{t('events.transfer.select')}</option>
          {events.map((e) => (
            <option key={e.id} value={e.id}>{e.name}</option>
          ))}
        </select>
      )}

      {(!showSourceSelect || sourceId) && (
        <div className="rounded-card border p-3 space-y-2" style={{ borderColor: 'var(--card-border)' }}>
          <p className="text-[10px] uppercase tracking-caps font-semibold" style={{ color: 'var(--text-subtle)' }}>
            {t('events.transfer.what')}
          </p>
          {COPY_GROUPS.map((key) => (
            <label key={key} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={!!opts[key]}
                onChange={() => toggle(key)}
                className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold shrink-0"
              />
              <span className="text-xs" style={{ color: 'var(--text-primary)' }}>
                {t(`events.transfer.group.${key}`)}
              </span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
