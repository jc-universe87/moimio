import { useMemo, useState } from 'react';
import ReasonButton from './ReasonButton';
import {
  reasoningLineExtended,
  unplacedReasoningLine,
} from '../services/placementReason';
import { useI18n } from '../hooks/useI18n';

/**
 * ReviewSurface — in-place "Was / Will be" allocation review.
 *
 * v0.70d-1 (R1 Phase 1): replaces the modal review that sat on top of
 * the board in v0.70c. This surface is shown IN PLACE of the board
 * while a proposal is pending, so the organiser has the full viewport
 * to compare current state to proposed state before committing.
 *
 * Structure (see R1-review-surface-spec.md for the full design doc):
 *
 *   ┌─ Top bar (sticky) ──────────────────┐
 *   │ Title + stats + [Commit] [Discard]  │
 *   └─────────────────────────────────────┘
 *   ⚠ Unplaced block (burgundy) — if any
 *   ⚠ Gender-unknown block (burgundy) — if any
 *   ─────────────────────────────────────
 *   Room A
 *   Was (3)          Will be (4) · +1
 *   [names...]       [names...]
 *
 *   Room B
 *   Was (4)          Will be (3) · −1
 *   ...
 *
 * Every participant name is a ReasonButton that reveals the engine's
 * placement reasoning on hover (desktop) or tap (mobile bottom sheet).
 *
 * Props:
 *   proposal         — the full proposal object from catApi.suggest()
 *                      { proposed: {unitId: [pid, ...]},
 *                        placement_reasons: {pid: {reason, ...}},
 *                        unplaced: [pid, ...],
 *                        stats: {...},
 *                        units: [{id, name, ...}],
 *                        run_id }
 *   existingUnits    — array of unit metadata objects (id, name,
 *                      capacity, occupant_count, ...). Shape matches
 *                      AllocationBoard's `units` state. The members
 *                      themselves live in `allMembers` (see below).
 *   allMembers       — map keyed by unitId (as string) to array of
 *                      allocation records `{participant_id, ...}`.
 *                      Shape matches AllocationBoard's `allMembers`
 *                      state (populated by allocApi.byCategory).
 *                      This is the source of truth for "Was" —
 *                      v0.70d-1-1 fix: the previous version assumed
 *                      occupants were on the unit object, they're not.
 *   participantList  — for name lookups (pid → participant)
 *   committing       — boolean, locks buttons while commit in flight
 *   onCommit         — ()=>void, parent handles the API call
 *   onDiscard        — ()=>void, parent clears proposal state.
 *                      ALWAYS called via the confirm dialog below
 *                      (per R1 Q1 resolution — always-confirm).
 */
export default function ReviewSurface({
  proposal,
  existingUnits,
  allMembers,
  participantList,
  committing,
  onCommit,
  onDiscard,
}) {
  const { t } = useI18n();
  const [discardConfirm, setDiscardConfirm] = useState(false);

  // Index participants by id for O(1) name/number lookup inside
  // the busy render path below.
  const participantById = useMemo(() => {
    const m = new Map();
    for (const p of participantList || []) m.set(String(p.id), p);
    return m;
  }, [participantList]);

  // Build a unified set of unit ids that appear in Was OR Will-be.
  // Preserve order: existing units first (in their current order),
  // then any new units from the proposal. `proposal.units` provides
  // ordering for new ones; fall back to unit id as the last resort.
  const allUnits = useMemo(() => {
    const seen = new Set();
    const rows = [];
    for (const u of existingUnits || []) {
      const id = String(u.id);
      seen.add(id);
      rows.push({ id, unit: u });
    }
    const proposedIds = Object.keys(proposal?.proposed || {});
    for (const pid of proposedIds) {
      if (seen.has(pid)) continue;
      seen.add(pid);
      const u = (proposal.units || []).find(x => String(x.id) === pid);
      rows.push({ id: pid, unit: u });
    }
    return rows;
  }, [existingUnits, proposal]);

  // Pre-compute "was" occupants per unit from allMembers
  // (v0.70d-1-1 fix: was previously reading `u.occupants`, which
  // doesn't exist — the API returns `occupant_count` scalar only,
  // and the actual members live in the sibling `allMembers` state
  // keyed by unitId. See AllocationBoard.loadAll.)
  const wasByUnit = useMemo(() => {
    const m = new Map();
    for (const u of existingUnits || []) {
      const uid = String(u.id);
      const members = (allMembers && allMembers[uid]) || [];
      // Each member record has `.participant_id` (see AllocationBoard
      // consumers e.g. allMembers[...].some(m => m.participant_id === pid)).
      const ids = members
        .map(x => x?.participant_id != null ? String(x.participant_id) : null)
        .filter(Boolean);
      m.set(uid, ids);
    }
    return m;
  }, [existingUnits, allMembers]);

  // Friendly lookup for "Will be" ids — straight from proposal.proposed.
  const willByUnit = useMemo(() => {
    const m = new Map();
    for (const [uid, pids] of Object.entries(proposal?.proposed || {})) {
      m.set(String(uid), pids.map(String));
    }
    return m;
  }, [proposal]);

  const renderName = (pid, variant) => {
    const p = participantById.get(String(pid));
    if (!p) return null;
    const reasonMeta = proposal?.placement_reasons?.[String(pid)];
    // v0.73a: when rendering an unplaced chip, pass the engine's
    // unplaced_reasons[pid] meta so the reason line dispatches on
    // the new reason tags (gender_unknown_no_mixed_unit_available,
    // cluster_oversized_split_disabled, no_capacity_remaining).
    const unplacedMeta = proposal?.unplaced_reasons?.[String(pid)];
    const reasoning = variant === 'unplaced'
      ? unplacedReasoningLine(t, unplacedMeta)
      : reasoningLineExtended(reasonMeta, t);
    return (
      <ReasonButton
        key={pid}
        name={`${p.first_name} ${p.last_name}`}
        participantNumber={p.participant_number}
        reasoning={reasoning}
        variant={variant}
        pending={p.registration_status === 'pending'}
        t={t}
      />
    );
  };

  // For each row, compute the delta label: "+N", "−N", "unchanged",
  // or "new room" when Was is empty. Quiet copy — the numbers carry
  // the signal.
  const deltaLabel = (wasN, willN) => {
    if (wasN === 0 && willN > 0) return t('engine.review.new_room');
    if (wasN === willN) return t('engine.review.delta_zero');
    const diff = willN - wasN;
    return diff > 0
      ? t('engine.review.delta_plus', { n: diff })
      : t('engine.review.delta_minus', { n: -diff });
  };

  const handleDiscardClick = () => setDiscardConfirm(true);
  const handleDiscardConfirm = () => { setDiscardConfirm(false); onDiscard(); };
  const handleDiscardCancel  = () => setDiscardConfirm(false);

  // Stats line — R8a: all stats in muted text, numbers carry signal.
  // No amber, no green. Mark-clusters call-out uses io-accent (that's
  // a neutral accent, not a success signal — it just tints the number
  // that organisers tend to look for).
  const stats = proposal?.stats || {};
  const placedLine = t('engine.stats.placed', {
    n: stats.placed ?? 0,
    total: stats.total ?? 0,
  });

  return (
    <div className="relative max-w-5xl mx-auto">
      {/* ─── Sticky top bar ─── */}
      <div
        className="sticky top-0 z-20 card-surface-solid rounded-2xl p-4 mb-4"
        style={{ border: '1px solid var(--card-border)' }}
      >
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div className="min-w-0 flex-1">
            <h2 className="font-heading font-bold text-lg"
                style={{ color: 'var(--text-primary)' }}>
              {t('engine.review_title')}
            </h2>
            <p className="text-xs mt-1 leading-snug"
               style={{ color: 'var(--text-muted)' }}>
              {placedLine}
              {stats.clusters_total > 0 && (
                <> · {t('engine.stats.clusters_intact', { n: stats.clusters_kept_whole })}</>
              )}
              {stats.clusters_split > 0 && (
                <> · {t('engine.stats.clusters_split', { n: stats.clusters_split })}</>
              )}
              {stats.mark_clusters > 0 && (
                <> · {t('engine.stats.mark_clusters', { n: stats.mark_clusters })}</>
              )}
            </p>
          </div>
          <div className="flex gap-2 shrink-0">
            <button
              type="button"
              onClick={onCommit}
              disabled={committing}
              className="text-sm font-semibold px-4 py-2 rounded-card transition-colors disabled:opacity-50"
              style={{
                background: 'var(--io-accent)',
                color: 'var(--on-accent)',
              }}
            >
              {committing ? t('engine.committing') : t('engine.commit')}
            </button>
            <button
              type="button"
              onClick={handleDiscardClick}
              disabled={committing}
              className="text-sm font-medium px-4 py-2 rounded-card border transition-colors hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-50"
              style={{
                borderColor: 'var(--card-border)',
                color: 'var(--text-muted)',
              }}
            >
              {t('engine.discard')}
            </button>
          </div>
        </div>
      </div>

      {/* ─── Unplaced warning ─── */}
      {proposal.unplaced && proposal.unplaced.length > 0 && (
        <div
          className="rounded-2xl p-4 mb-3"
          style={{
            background: 'var(--alert-tint)',
            border: '1px solid var(--alert-border)',
          }}
        >
          <p className="text-xs font-semibold mb-2"
             style={{ color: 'var(--alert-burgundy)' }}>
            {t('engine.unplaced', { n: proposal.unplaced.length })}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {proposal.unplaced.map(pid => renderName(pid, 'unplaced'))}
          </div>
        </div>
      )}

      {/* ─── Gender-unknown warning ─── */}
      {(proposal.stats?.gender_unknown_placement_ids?.length ?? 0) > 0 && (
        <div
          className="rounded-2xl p-4 mb-3"
          style={{
            background: 'var(--alert-tint)',
            border: '1px solid var(--alert-border)',
          }}
        >
          <p className="text-xs font-semibold mb-2"
             style={{ color: 'var(--alert-burgundy)' }}>
            {t('engine.gender_unknown_warning', {
              n: proposal.stats.gender_unknown_placement_ids.length,
            })}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {proposal.stats.gender_unknown_placement_ids.map(
              pid => renderName(pid, 'gender-unknown')
            )}
          </div>
        </div>
      )}

      {/* ─── Room-by-room comparison ─── */}
      <div className="space-y-4">
        {allUnits.map(({ id: uid, unit }) => {
          const wasIds  = wasByUnit.get(uid) || [];
          const willIds = willByUnit.get(uid) || [];
          const unitName = unit?.name || uid.slice(0, 8);
          const delta = deltaLabel(wasIds.length, willIds.length);

          // Compute "new" / "leaving" annotations by set membership.
          const willSet = new Set(willIds.map(String));
          const wasSet  = new Set(wasIds.map(String));

          return (
            <div
              key={uid}
              className="card-surface-solid rounded-2xl p-4"
              style={{ border: '1px solid var(--card-border)' }}
            >
              <h3 className="font-heading font-bold text-sm mb-3"
                  style={{ color: 'var(--text-primary)' }}>
                {unitName}
              </h3>

              {/* Was on the left, Will-be on the right. v0.70d-1-3:
                  dropped `md:grid-cols-2` because the forced 50/50
                  split left acres of empty space between a 1-chip Was
                  and a 1-chip Will-be on wide viewports. `md:flex` with
                  content-based sizing lets short entries sit close
                  together for easy scanning; when chip counts grow, the
                  Will-be column gets a min-width floor so Was doesn't
                  starve it of space. */}
              <div className="md:flex md:flex-wrap md:items-start md:gap-x-8 md:gap-y-3 space-y-4 md:space-y-0">
                {/* Was */}
                <div className="md:min-w-[12rem]">
                  <p className="text-[10px] uppercase tracking-caps font-semibold mb-2"
                     style={{ color: 'var(--text-subtle)' }}>
                    {t('engine.review.was')}
                    {' '}({wasIds.length === 0 ? '—' : wasIds.length})
                  </p>
                  {wasIds.length === 0 ? (
                    <p className="text-xs italic"
                       style={{ color: 'var(--text-subtle)' }}>
                      —
                    </p>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {wasIds.map(pid => {
                        const p = participantById.get(String(pid));
                        if (!p) return null;
                        const leaving = !willSet.has(String(pid));
                        return (
                          <span key={pid}
                                className="inline-flex items-center gap-1">
                            {/* Was-side names are NOT ReasonButtons —
                                the reasoning belongs to the Will-be
                                placement, not the historical state.
                                Render as a plain chip.
                                v0.73c: pending status is layered on
                                top of the leaving styling. Two
                                composable visual signals (line-
                                through means "leaving"; italic means
                                "pending"). */}
                            <span
                              className="text-xs px-2 py-0.5 rounded-full"
                              title={p.registration_status === 'pending' ? t('organise.pending_pill.tooltip') : undefined}
                              style={{
                                background: 'var(--neutral-tint)',
                                color: 'var(--text-muted)',
                                textDecoration: leaving ? 'line-through' : undefined,
                                opacity: leaving ? 0.65 : (p.registration_status === 'pending' ? 0.7 : 1),
                                fontStyle: p.registration_status === 'pending' ? 'italic' : undefined,
                              }}
                            >
                              {p.first_name} {p.last_name}
                            </span>
                            {leaving && (
                              <span className="text-[10px]"
                                    style={{ color: 'var(--text-subtle)' }}>
                                ← {t('engine.review.leaving_annotation')}
                              </span>
                            )}
                          </span>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Will be */}
                <div className="md:min-w-[12rem]">
                  <p className="text-[10px] uppercase tracking-caps font-semibold mb-2"
                     style={{ color: 'var(--text-subtle)' }}>
                    {t('engine.review.will_be')}
                    {' '}({willIds.length === 0 ? '—' : willIds.length})
                    {delta && (
                      <span className="ml-2 font-normal normal-case"
                            style={{
                              color: 'var(--text-subtle)',
                              letterSpacing: 'normal',
                            }}>
                        {delta}
                      </span>
                    )}
                  </p>
                  {willIds.length === 0 ? (
                    <p className="text-xs italic"
                       style={{ color: 'var(--text-subtle)' }}>
                      —
                    </p>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {willIds.map(pid => {
                        const isNew = !wasSet.has(String(pid));
                        return (
                          <span key={pid}
                                className="inline-flex items-center gap-1">
                            {renderName(pid, 'placed')}
                            {isNew && (
                              <span className="text-[10px]"
                                    style={{ color: 'var(--text-subtle)' }}>
                                ← {t('engine.review.new_annotation')}
                              </span>
                            )}
                          </span>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* ─── Discard confirm dialog (always shown, per R1 Q1) ─── */}
      {discardConfirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(0,0,0,0.5)' }}
          onClick={handleDiscardCancel}
        >
          <div
            className="card-surface-solid rounded-2xl max-w-md w-full p-6"
            style={{ border: '1px solid var(--card-border)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="font-heading font-bold text-lg mb-2"
                style={{ color: 'var(--text-primary)' }}>
              {t('engine.review.discard_confirm_title')}
            </h3>
            <p className="text-sm mb-5" style={{ color: 'var(--text-muted)' }}>
              {t('engine.review.discard_confirm_body')}
            </p>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={handleDiscardCancel}
                className="text-xs font-medium px-4 py-2 rounded-card border"
                style={{
                  borderColor: 'var(--card-border)',
                  color: 'var(--text-muted)',
                }}
              >
                {t('common.cancel')}
              </button>
              <button
                type="button"
                onClick={handleDiscardConfirm}
                className="text-xs font-semibold px-4 py-2 rounded-card"
                style={{
                  background: 'var(--alert-burgundy)',
                  color: '#fff',
                }}
              >
                {t('engine.discard')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
