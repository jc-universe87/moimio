/**
 * RegistrationPhasePage — the admin/organiser landing during Registration phase.
 *
 * Replaces the v45 event dashboard for this phase. Dashboard-style: watch
 * state, act on "close registration" when ready, share the form, review
 * recent sign-ups and anything needing attention.
 *
 * Content (top to bottom):
 *   1. Event header (reused pattern — name + phase strip + stats)
 *   2. Primary CTA — "Close registration" prominent button + "Share form" outline button
 *   3. Stats + sparkline hero
 *   4. Attention queue (conditional — only if something needs attention)
 *   5. Recent sign-ups (togglable; default visible)
 *   6. "View all participants →" link
 *
 * v50d-2 work (future): "More" menu for re-accessing Group types, Marks,
 * Staff settings mid-registration.
 */

import { useMemo, useState } from 'react';
import { events as eventsApi } from '../services/api';
import { useI18n } from '../hooks/useI18n';
import Sparkline from '../components/Sparkline';
import ShareFormModal from '../components/ShareFormModal';
import EmptyState from '../components/EmptyState';

import TranslatedError from '../components/TranslatedError';
// Adaptive sparkline window: if the event record was created less than
// 7 days ago, show all-time; otherwise show last 7 days. Returns
// { days, label, points } — days is an array of Date objects (oldest first,
// daily buckets), label is the translation key for the sparkline heading,
// points is the {date, count}[] for the Sparkline component.
// v1.0.1e-23: window is selectable — '7d', '30d', or 'all' (since the event
// was created). 7d/30d are clamped to the creation date so a young event
// never shows empty leading days. Returns the daily points plus the total
// sign-ups in the window (for the summary line).
function buildSparkline(participantList, eventCreatedAt, range) {
  const now = new Date();
  const createdMs = eventCreatedAt ? new Date(eventCreatedAt).getTime() : now.getTime();
  const DAY = 24 * 60 * 60 * 1000;
  let startMs;
  if (range === 'all') startMs = createdMs;
  else if (range === '30d') startMs = Math.max(createdMs, now.getTime() - 30 * DAY);
  else startMs = Math.max(createdMs, now.getTime() - 7 * DAY); // '7d' default

  const start = new Date(startMs);
  start.setHours(0, 0, 0, 0);
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const buckets = [];
  for (let d = new Date(start); d <= today; d.setDate(d.getDate() + 1)) {
    buckets.push(new Date(d));
  }

  let total = 0;
  const points = buckets.map(b => {
    const bNext = new Date(b);
    bNext.setDate(bNext.getDate() + 1);
    const count = participantList.filter(p => {
      if (p.registration_status === 'cancelled') return false;
      if (!p.created_at) return false;
      const ms = new Date(p.created_at).getTime();
      return ms >= b.getTime() && ms < bNext.getTime();
    }).length;
    total += count;
    return { date: b.toISOString(), count };
  });

  return { points, total };
}

// Relative time for recent sign-ups ("5 min ago", "2 h ago", "3 d ago")
function relativeTime(iso, t) {
  if (!iso) return '';
  const ms = Date.now() - new Date(iso).getTime();
  const min = Math.floor(ms / 60000);
  if (min < 1) return t('reg_phase.time.just_now');
  if (min < 60) return t('reg_phase.time.minutes', { n: min });
  const hrs = Math.floor(min / 60);
  if (hrs < 24) return t('reg_phase.time.hours', { n: hrs });
  const days = Math.floor(hrs / 24);
  return t('reg_phase.time.days', { n: days });
}

export default function RegistrationPhasePage({
  event,
  participantList,
  isAdmin,
  isStaff,
  staffPerms,
  onEventChange,
  goToSection,
}) {
  const { t } = useI18n();

  // v1.0-pre #10: who can see the "Set up the check-in panel" link
  // during Registration phase. Admins always; staff only if their
  // assignment grants the new pre_event sub-flag on checkin. The
  // staffPerms object follows the α-shape: checkin = {access, pre_event}.
  // Tolerates the legacy flat-string by reading false for pre_event.
  const checkinPreEventVisible = isAdmin || (() => {
    if (!isStaff || !staffPerms) return false;
    const c = staffPerms.checkin;
    return !!(c && typeof c === 'object' && c.access && c.pre_event);
  })();

  // Controls
  const [closing, setClosing] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);
  const [recentVisible, setRecentVisible] = useState(true);
  const [range, setRange] = useState('7d'); // sparkline window: 7d | 30d | all
  const [error, setError] = useState(null);

  // Derived participant stats
  const activeList = useMemo(
    () => participantList.filter(p => p.registration_status !== 'cancelled'),
    [participantList]
  );
  const confirmedCount = useMemo(
    () => participantList.filter(p => p.registration_status === 'confirmed').length,
    [participantList]
  );
  const pendingCount = useMemo(
    () => participantList.filter(p => p.registration_status === 'pending').length,
    [participantList]
  );
  const cancelledCount = useMemo(
    () => participantList.filter(p => p.registration_status === 'cancelled').length,
    [participantList]
  );

  // Recent sign-ups — last 5 by created_at desc, confirmed or pending
  const recent = useMemo(() => {
    return [...activeList]
      .filter(p => p.created_at)
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      .slice(0, 5);
  }, [activeList]);

  // Sparkline data
  const spark = useMemo(
    () => buildSparkline(participantList, event?.created_at, range),
    [participantList, event?.created_at, range]
  );

  const handleClose = async () => {
    if (!event) return;
    setClosing(true);
    try {
      const updated = await eventsApi.closeRegistration(event.id);
      onEventChange?.(updated);
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('moimio:event-changed'));
      }
    } catch (err) {
      setError(err);
    } finally {
      setClosing(false);
    }
  };

  const shareUrl = `${window.location.origin}/register/${event?.id}`;
  const registeredCount = activeList.length;
  const isEmpty = registeredCount === 0;

  return (
    <div className="space-y-6">
      <TranslatedError err={error} className="p-3 rounded-card text-sm" />

      {/* ─── Primary action row ──────────────────────────────────────── */}
      {/* v0.50o: restructured so the "No new sign-ups will be accepted"
          hint sits adjacent to the Close button (the action it describes)
          rather than after the Share button where it read as if it
          belonged to Share. */}
      {isAdmin && (
        <div
          className="card-surface-solid rounded-2xl p-4 sm:px-5 sm:py-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
          style={{ border: '1px solid var(--card-border)' }}
        >
          <button
            type="button"
            onClick={() => setShareOpen(true)}
            className="inline-flex items-center justify-center gap-2 text-sm font-medium px-4 py-2.5 rounded-card border hover:bg-black/5 dark:hover:bg-white/10 self-stretch sm:self-auto shrink-0"
            style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" />
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" /><line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
            </svg>
            {t('reg_phase.share.button')}
          </button>
          <div className="flex flex-col items-stretch sm:items-end gap-1.5 min-w-0">
            <button
              type="button"
              onClick={handleClose}
              disabled={closing}
              className="text-sm font-semibold px-5 py-2.5 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 disabled:opacity-50 whitespace-nowrap"
            >
              {closing ? t('reg_phase.closing') : t('reg_phase.close.button')} →
            </button>
            <p className="text-xs sm:text-right" style={{ color: 'var(--text-subtle)' }}>
              {t('reg_phase.close.hint')}
            </p>
          </div>
        </div>
      )}

      {/* ─── v1.0-pre #10: pre-event check-in setup link ──────────────── */}
      {/* Subtle secondary link (Option 1). Visible to admins always; to
          staff only when their assignment has checkin.pre_event=true.
          Routes to the Check-in section, where they can configure the
          custom tick-off columns ahead of arrivals. */}
      {checkinPreEventVisible && (
        <div className="-mt-1 mb-2">
          <button
            type="button"
            onClick={() => goToSection('checkin')}
            className="text-sm font-medium hover:underline"
            style={{ color: 'var(--io-accent)' }}
          >
            → {t('reg_phase.checkin_pre_event_link')}
          </button>
        </div>
      )}

      {/* ─── Stats + sparkline ───────────────────────────────────────── */}
      <div className="card-surface-solid rounded-2xl p-5" style={{ border: '1px solid var(--card-border)' }}>
        {isEmpty ? (
          <div className="text-center py-6">
            <p className="font-heading text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
              {t('reg_phase.empty.title')}
            </p>
            <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
              {t('reg_phase.empty.hint')}
            </p>
          </div>
        ) : (
          <>
            <div className="flex flex-wrap items-end gap-6 mb-4">
              <div>
                <p className="text-[10px] uppercase tracking-caps font-semibold" style={{ color: 'var(--text-subtle)' }}>
                  {t('reg_phase.registered')}
                </p>
                <p className="font-heading font-bold text-4xl" style={{ color: 'var(--text-primary)' }}>
                  {registeredCount}
                </p>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-caps font-semibold" style={{ color: 'var(--text-subtle)' }}>
                  {t('reg_phase.confirmed')}
                </p>
                <p className="font-heading font-semibold text-xl" style={{ color: 'var(--text-primary)' }}>
                  {confirmedCount}
                </p>
              </div>
              {pendingCount > 0 && (
                <div>
                  <p className="text-[10px] uppercase tracking-caps font-semibold" style={{ color: 'var(--text-subtle)' }}>
                    {t('reg_phase.pending')}
                  </p>
                  <p className="font-heading font-semibold text-xl" style={{ color: 'var(--text-primary)' }}>
                    {pendingCount}
                  </p>
                </div>
              )}
              {cancelledCount > 0 && (
                <div>
                  <p className="text-[10px] uppercase tracking-caps font-semibold" style={{ color: 'var(--text-subtle)' }}>
                    {t('reg_phase.cancelled')}
                  </p>
                  <p className="font-heading font-semibold text-xl" style={{ color: 'var(--text-muted)' }}>
                    {cancelledCount}
                  </p>
                </div>
              )}
            </div>
            <div className="flex items-end justify-between gap-3 mb-2">
              <div className="min-w-0">
                <p className="text-[10px] uppercase tracking-caps font-semibold" style={{ color: 'var(--text-subtle)' }}>
                  {t('reg_phase.sparkline.title')}
                </p>
                <p className="text-sm font-body" style={{ color: 'var(--text-muted)' }}>
                  {t('reg_phase.sparkline.total', { n: spark.total })}
                </p>
              </div>
              <div className="inline-flex rounded-card overflow-hidden border shrink-0" style={{ borderColor: 'var(--card-border)' }}>
                {['7d', '30d', 'all'].map(r => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setRange(r)}
                    aria-pressed={range === r}
                    className="px-2.5 py-1 text-xs font-medium transition-colors"
                    style={range === r
                      ? { background: 'var(--io-accent)', color: '#fff' }
                      : { color: 'var(--text-muted)', background: 'transparent' }}
                  >
                    {t(`reg_phase.range.${r}`)}
                  </button>
                ))}
              </div>
            </div>
            <Sparkline points={spark.points} height={64} label={t('reg_phase.sparkline.title')} />
          </>
        )}
      </div>

      {/* ─── Attention queue — pending confirmations ─────────────────── */}
      {pendingCount > 0 && isAdmin && (
        <div
          className="card-surface-solid rounded-2xl p-4 flex items-start gap-3"
          style={{
            // Order matters: borderLeft must come AFTER border shorthand,
            // otherwise the shorthand overwrites it. Safer still: set each
            // side explicitly so there's no shorthand to fight with.
            borderTop: '1px solid var(--card-border)',
            borderRight: '1px solid var(--card-border)',
            borderBottom: '1px solid var(--card-border)',
            borderLeft: '4px solid var(--alert-burgundy)',
          }}
        >
          <div className="flex-1 min-w-0">
            <p className="text-[10px] uppercase tracking-caps font-semibold mb-0.5" style={{ color: 'var(--text-subtle)' }}>
              {t('reg_phase.attention.title')}
            </p>
            <p className="font-body font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
              {t('reg_phase.attention.pending_confirm', { n: pendingCount })}
            </p>
          </div>
          <button
            type="button"
            onClick={() => goToSection('people', { status: 'pending' })}
            className="text-xs font-semibold px-3 py-1.5 rounded-card border hover:bg-black/5 dark:hover:bg-white/10 whitespace-nowrap shrink-0"
            style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}
          >
            {t('reg_phase.attention.review_link')} →
          </button>
        </div>
      )}

      {/* ─── Recent sign-ups ─────────────────────────────────────────── */}
      {!isEmpty && (
        <div className="card-surface-solid rounded-2xl" style={{ border: '1px solid var(--card-border)' }}>
          <div className="px-5 py-3 flex items-center justify-between">
            <p className="text-[10px] uppercase tracking-caps font-semibold" style={{ color: 'var(--text-subtle)' }}>
              {t('reg_phase.recent.title')}
            </p>
            <button
              type="button"
              onClick={() => setRecentVisible(v => !v)}
              className="text-xs font-medium hover:underline"
              style={{ color: 'var(--text-muted)' }}
            >
              {recentVisible ? t('reg_phase.recent.toggle_hide') : t('reg_phase.recent.toggle_show')}
            </button>
          </div>
          {recentVisible && (
            <div style={{ borderTop: '1px solid var(--card-border)' }}>
              {recent.length === 0 ? (
                <div className="p-5">
                  <EmptyState
                    compact
                    title={t('reg_phase.recent.empty.title')}
                    hint={t('reg_phase.recent.empty.hint')}
                  />
                </div>
              ) : (
                <ul>
                  {recent.map(p => (
                    <li
                      key={p.id}
                      className="px-5 py-2.5 flex items-center justify-between gap-3 text-sm"
                      style={{ borderTop: '1px solid var(--card-border)' }}
                    >
                      <span className="font-medium truncate" style={{ color: 'var(--text-primary)' }}>
                        {p.first_name} {p.last_name}
                      </span>
                      <span className="text-xs shrink-0" style={{ color: 'var(--text-subtle)' }}>
                        {relativeTime(p.created_at, t)}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              <div className="px-5 py-3" style={{ borderTop: '1px solid var(--card-border)' }}>
                <button
                  type="button"
                  onClick={() => goToSection('people')}
                  className="text-xs font-medium hover:underline"
                  style={{ color: 'var(--io-accent)' }}
                >
                  {t('reg_phase.recent.view_all')} ({registeredCount}) →
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {shareOpen && (
        <ShareFormModal
          url={shareUrl}
          eventName={event?.name}
          onClose={() => setShareOpen(false)}
        />
      )}
    </div>
  );
}
