import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { events as eventsApi } from '../services/api';
import { useI18n } from '../hooks/useI18n';

import TranslatedError from '../components/TranslatedError';
/**
 * DuplicateEventPage — editable preview shown before creating a duplicate.
 *
 * v0.51 design (spec §14, Option A2):
 *   - Pre-fill form from source event (name + " (copy)", description,
 *     location, timezone). Dates BLANK.
 *   - Show a summary card below the form with config counts fetched
 *     from /duplicate/counts.
 *   - Nothing is written until the user clicks "Create duplicate".
 *     Cancel leaves nothing behind.
 *
 * Route: /admin/events/duplicate/:sourceId
 */
export default function DuplicateEventPage() {
  const { sourceId } = useParams();
  const navigate = useNavigate();
  const { t } = useI18n();

  const [source, setSource] = useState(null);
  const [counts, setCounts] = useState(null);
  const [form, setForm] = useState({
    name: '', description: '', location: '', start_date: '', end_date: '', timezone: '',
  });
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);

  // ── Load source event + counts ──────────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [ev, c] = await Promise.all([
          eventsApi.get(sourceId),
          eventsApi.duplicateCounts(sourceId),
        ]);
        if (cancelled) return;
        setSource(ev);
        setCounts(c);
        const copySuffix = t('events.duplicate.name_suffix');
        setForm({
          name: `${ev.name}${copySuffix}`,
          description: ev.description || '',
          location: ev.location || '',
          start_date: '',
          end_date: '',
          timezone: ev.timezone || '',
        });
      } catch (err) {
        if (!cancelled) setError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [sourceId, t]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      const payload = {
        name: form.name,
        copy_from_event_id: sourceId,
      };
      if (form.description) payload.description = form.description;
      if (form.location) payload.location = form.location;
      if (form.start_date) payload.start_date = form.start_date;
      if (form.end_date) payload.end_date = form.end_date;
      if (form.timezone) payload.timezone = form.timezone;
      const created = await eventsApi.create(payload);
      navigate(`/admin/events/${created.id}`);
    } catch (err) {
      setError(err);
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-2xl">
        <p className="text-sm" style={{ color: 'var(--text-subtle)' }}>{t('common.loading')}</p>
      </div>
    );
  }

  if (error && !source) {
    return (
      <div className="max-w-2xl">
        <TranslatedError err={error} />
        <Link to="/admin/events" className="text-sm text-steel-blue hover:underline">
          ← {t('common.back')}
        </Link>
      </div>
    );
  }

  const countItems = [
    { n: counts?.marks ?? 0,                 key: 'events.duplicate.count.marks'      },
    { n: counts?.field_configs ?? 0,         key: 'events.duplicate.count.fields'     },
    { n: counts?.custom_fields ?? 0,         key: 'events.duplicate.count.custom'     },
    { n: counts?.allocation_categories ?? 0, key: 'events.duplicate.count.group_types' },
    { n: counts?.staff_assignments ?? 0,     key: 'events.duplicate.count.staff'      },
  ];

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <Link
          to="/admin/events"
          className="text-xs font-medium hover:underline"
          style={{ color: 'var(--text-subtle)' }}
        >
          ← {t('events.title')}
        </Link>
        <h1 className="font-heading text-2xl font-bold mt-1" style={{ color: 'var(--text-primary)' }}>
          {(t('events.duplicate.title')).replace('{name}', source?.name || '')}
        </h1>
      </div>

      <TranslatedError err={error} />

      <form onSubmit={handleSubmit} className="space-y-4">
        <div
          className="card-surface-solid rounded-2xl p-5 space-y-3"
          style={{ border: '1px solid var(--card-border)' }}
        >
          <input
            type="text" required value={form.name}
            onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
            placeholder={t('events.name') + ' *'}
            className="w-full rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]"
          />
          <textarea
            rows={2} value={form.description}
            onChange={e => setForm(p => ({ ...p, description: e.target.value }))}
            placeholder={t('events.description')}
            className="w-full rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)] resize-none"
          />
          <input
            type="text" value={form.location}
            onChange={e => setForm(p => ({ ...p, location: e.target.value }))}
            placeholder={t('events.location')}
            className="w-full rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]"
          />
          <div className="flex gap-2">
            <input
              type="date" value={form.start_date}
              onChange={e => setForm(p => ({ ...p, start_date: e.target.value }))}
              className="flex-1 rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]"
            />
            <input
              type="date" value={form.end_date}
              onChange={e => setForm(p => ({ ...p, end_date: e.target.value }))}
              className="flex-1 rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]"
            />
          </div>
        </div>

        {/* Summary card — what will be copied */}
        {counts && (
          <div
            className="card-surface-solid rounded-2xl p-5"
            style={{ border: '1px solid var(--card-border)' }}
          >
            <p className="text-xs font-semibold mb-2 uppercase tracking-caps" style={{ color: 'var(--text-subtle)' }}>
              {t('events.duplicate.will_copy')}
            </p>
            <ul className="text-sm space-y-1" style={{ color: 'var(--text-primary)' }}>
              {countItems.map(item => (
                <li key={item.key}>
                  · {t(item.key).replace('{n}', item.n)}
                </li>
              ))}
            </ul>
            <p className="text-[10px] mt-3" style={{ color: 'var(--text-subtle)' }}>
              {t('events.duplicate.will_copy.hint')}
            </p>
          </div>
        )}

        <div className="flex gap-2 justify-end">
          <Link
            to="/admin/events"
            className="text-sm font-medium px-4 py-2 rounded-card border hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
            style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}
          >
            {t('common.cancel')}
          </Link>
          <button
            type="submit"
            disabled={creating || !form.name.trim()}
            className="text-sm font-semibold px-4 py-2 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 disabled:opacity-50 transition-colors"
          >
            {creating
              ? (t('events.duplicate.creating'))
              : (t('events.duplicate.submit'))}
          </button>
        </div>
      </form>
    </div>
  );
}
