import { useState, useEffect } from 'react';
import { preferenceRequests as prefApi } from '../services/api';
import { useI18n } from '../hooks/useI18n';

export default function PreferencesPanel({ eventId, isAdmin }) {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // 'all' | 'pending' | 'resolved'
  // v0.58e-1: collapse the preferences block by default. Expanded state
  // persists per-mount; organiser opens once, works through, closes.
  const [isExpanded, setIsExpanded] = useState(false);
  const { t } = useI18n();

  useEffect(() => { load(); }, [eventId]);

  const load = async () => {
    try {
      const data = await prefApi.list(eventId);
      setRequests(data);
    } catch {} finally { setLoading(false); }
  };

  const toggleResolved = async (req) => {
    try {
      const updated = await prefApi.resolve(eventId, req.id, { resolved: !req.resolved });
      setRequests(prev => prev.map(r => r.id === req.id ? updated : r));
    } catch {}
  };

  const filtered = requests.filter(r =>
    filter === 'all' ? true :
    filter === 'pending' ? !r.resolved :
    r.resolved
  );

  const pendingCount = requests.filter(r => !r.resolved).length;
  const hasPending = pendingCount > 0;

  if (loading) return null; // don't flash a loading row above the board
  if (requests.length === 0) return null; // nothing to review → no card at all

  // v0.58e-1: Burgundy left-stripe when there are pending items (matches
  // §9.1 "required / attention" semantics used by SetupCard).
  const stripeColor = hasPending ? 'var(--alert-burgundy)' : null;

  return (
    <div className="rounded-xl"
      style={{
        border: '1px solid var(--card-border)',
        borderLeft: stripeColor ? `4px solid ${stripeColor}` : '1px solid var(--card-border)',
        background: 'var(--card-bg-solid)',
      }}>
      {/* Collapsed header — always rendered, tap to toggle */}
      <button
        type="button"
        onClick={() => setIsExpanded(v => !v)}
        aria-expanded={isExpanded}
        className="w-full text-left px-4 py-3 flex items-center gap-3"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-body font-bold text-sm" style={{ color: 'var(--text-primary)' }}>
              {t('prefs.admin_panel')}
            </span>
            {hasPending && (
              <span className="text-[10px] uppercase tracking-caps font-bold"
                style={{ color: 'var(--alert-burgundy)' }}>
                {pendingCount} {t('prefs.pending')}
              </span>
            )}
            {!hasPending && requests.length > 0 && (
              <span className="text-[10px] uppercase tracking-caps font-semibold"
                style={{ color: 'var(--text-subtle)' }}>
                ✓ {t('prefs.all_resolved')}
              </span>
            )}
          </div>
          {!isExpanded && (
            <p className="text-xs mt-0.5"
              style={{ color: 'var(--text-subtle)' }}>
              {t('prefs.engine_hint')}
            </p>
          )}
        </div>
        <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"
          className="shrink-0 transition-transform"
          style={{
            color: 'var(--text-subtle)',
            transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
          }}>
          <path d="M3 4.5 L6 8 L9 4.5" fill="none" stroke="currentColor"
            strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {/* Expanded body */}
      {isExpanded && (
        <div className="border-t px-4 py-3"
          style={{ borderColor: 'var(--card-border)' }}>
          {/* Filter pills */}
          <div className="flex gap-1 mb-3 flex-wrap">
            {['all', 'pending', 'resolved'].map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`text-[10px] px-2.5 py-1 rounded-full font-medium transition-colors ${
                  filter === f ? 'bg-steel-blue text-white' : 'bg-neutral-tint text-muted hover:opacity-80'
                }`}>
                {t(`prefs.filter.${f}`)}
              </button>
            ))}
          </div>

          {filtered.length === 0 ? (
            <p className="text-sm text-center py-6" style={{ color: 'var(--text-subtle)' }}>
              {t('prefs.none')}
            </p>
          ) : (
            <div className="space-y-3">
              {filtered.map(req => (
                <div key={req.id}
                  className={`rounded-xl border p-4 transition-colors ${
                    req.resolved ? 'border-accent bg-accent-tint' : 'border-card bg-card-solid'
                  }`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      {/* Requester */}
                      <p className="text-sm font-semibold text-body">
                        {req.participant_number ? `#${String(req.participant_number).padStart(3,'0')} ` : ''}
                        {req.participant_name}
                      </p>
                      {/* Arrow */}
                      <p className="text-xs text-subtle mt-0.5">{t('prefs.wants_to_be_with')}</p>
                      {/* Target */}
                      <div className="mt-1 bg-neutral-tint rounded-lg p-2.5 text-xs text-body space-y-0.5">
                        {req.preferred_participant_number && (
                          <p><span className="font-mono font-bold text-accent">
                            #{String(req.preferred_participant_number).padStart(3,'0')}
                          </span></p>
                        )}
                        {req.preferred_name && <p className="font-semibold">{req.preferred_name}</p>}
                        {req.preferred_details && (
                          <p className="text-muted italic">{req.preferred_details}</p>
                        )}
                        {req.category_scope && req.category_scope !== 'all' && (
                          <p className="text-subtle text-[10px] mt-1">
                            {t('prefs.scope')}: {Array.isArray(req.category_scope)
                              ? req.category_scope.join(', ')
                              : req.category_scope}
                          </p>
                        )}
                      </div>
                    </div>
                    {isAdmin && (
                      <button onClick={() => toggleResolved(req)}
                        className={`shrink-0 text-[10px] font-semibold px-3 py-1.5 rounded-lg border transition-colors ${
                          req.resolved
                            ? 'border-accent text-accent bg-accent-tint hover:opacity-80'
                            : 'border-card text-muted hover:border-accent hover:text-accent'
                        }`}>
                        {req.resolved ? `✓ ${t('prefs.resolved')}` : t('prefs.mark_resolved')}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
