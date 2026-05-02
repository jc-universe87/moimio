import { useState, useEffect, useCallback } from 'react';
import { allocationCategories, formatErrorMessage } from '../services/api';
import AllocationBoard from './AllocationBoard';
import AllocStatusPill, { deriveAllocState, ALLOC_STATE } from './AllocStatusPill';
import { useConfirmOverlay } from './ConfirmOverlay';
import { useI18n } from '../hooks/useI18n';
import { useToast } from '../hooks/useToast';
import GroupTypesEditor from './GroupTypesEditor';

import ErrorBanner from './ErrorBanner';

// v0.61c-2: detect a pointer device with a fine-grained pointer
// (mouse, trackpad). Same predicate as in GroupTypesEditor — see the
// comment there for the rationale. We use this for drag-to-reorder
// gating because viewport-width (`isMobileView` below) fires `false`
// on landscape mobile and on phones with viewport ≥768 CSS px,
// causing the "DRAG TO REORDER" hint and the draggable attribute
// to surface on touch devices that swipe a card.
const HAS_FINE_POINTER = typeof window !== 'undefined'
  && typeof window.matchMedia === 'function'
  && window.matchMedia('(hover: hover) and (pointer: fine)').matches;

export default function OrganiseDashboard({ eventId, eventName, participantList, noteCounts, isAdmin, staffPerms, onDataChange }) {
  const [categories, setCategories] = useState([]);
  const [selectedCatId, setSelectedCatId] = useState(null);
  // v0.74a: openSettingsOnNav + triggerSuggestMode + showModePicker
  // state vars removed. Pre-v0.74a they were set by the per-row
  // Auto-Allocate split button on the group-type overview. The button
  // was removed in v0.74a (overview is pure navigation now), and the
  // state vars + AllocationBoard prop pass became dead code. The
  // openSettings + triggerSuggestMode props on AllocationBoard remain
  // available for any future caller that wants to pre-trigger the
  // engine on navigation.
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingCat, setEditingCat] = useState(null);
  const [dragCatId, setDragCatId] = useState(null);
  const [dragOverCatId, setDragOverCatId] = useState(null);
  const [manageOpen, setManageOpen] = useState(false); // collapsible manage section
  // v0.70d-1 R1: dead proposal / committing / handleCommit state
  // removed alongside the legacy modal. The real engine flow lives
  // in AllocationBoard; this dashboard only routes users into it.
  // v0.61c-2: removed isMobileView state + resize listener — drag-to-
  // reorder now uses HAS_FINE_POINTER (above), and there are no
  // remaining viewport-based decisions in this component. AllocationBoard
  // still keeps its own isMobileView for non-drag layout choices.
  const { confirm, ConfirmOverlay } = useConfirmOverlay();
  const { t } = useI18n();
  // v0.70d-1 R2: shared toast for non-fatal error surfaces (none in
  // this component today, but hook is imported at the component level
  // so the ToastHost can mount and react to errors surfaced from
  // children / effects in future ships).
  const { ToastHost } = useToast();

  useEffect(() => { loadCategories(); }, [eventId]);

  const loadCategories = useCallback(async () => {
    try {
      const data = await allocationCategories.list(eventId);
      setCategories(data);
    } catch (err) { setError(err); }
    finally { setLoading(false); }
  }, [eventId]);

  const handleReorderCats = async (fromId, toId) => {
    if (!fromId || !toId || fromId === toId) return;
    const ids = categories.map(c => c.id);
    const from = ids.indexOf(fromId);
    const to = ids.indexOf(toId);
    if (from === -1 || to === -1) return;
    const reordered = [...ids];
    reordered.splice(from, 1);
    reordered.splice(to, 0, fromId);
    setCategories(reordered.map(id => categories.find(c => c.id === id)));
    try { await allocationCategories.reorder(eventId, reordered); }
    catch { loadCategories(); }
    setDragCatId(null); setDragOverCatId(null);
  };

  const handleUpdateCat = async (e) => {
    e.preventDefault();
    if (!editingCat) return;
    try {
      await allocationCategories.update(eventId, editingCat.id, editingCat);
      setEditingCat(null);
      await loadCategories();
    } catch (err) { setError(err); }
  };

  const handleDeleteCat = async (catId) => {
    const ok = await confirm({
      title: t('organise.delete_group_type.title'),
      message: t('organise.delete_group_type.message'),
      confirmLabel: t('common.delete'),
      danger: true,
    });
    if (!ok) return;
    try {
      await allocationCategories.delete(eventId, catId);
      if (selectedCatId === catId) setSelectedCatId(null);
      await loadCategories();
    } catch (err) { setError(err); }
  };

  // v50c-3b: allocation lifecycle confirm/unconfirm.
  // Keyed by catId so multiple cards can show their own in-flight state.
  const [confirmingCatId, setConfirmingCatId] = useState(null);

  const handleConfirmCategory = async (catId, e) => {
    e?.stopPropagation?.();
    setConfirmingCatId(catId);
    try {
      await allocationCategories.confirm(eventId, catId);
      await loadCategories();
      onDataChange?.();
    } catch (err) {
      setError(err);
    } finally {
      setConfirmingCatId(null);
    }
  };

  // v0.50p: handleUnconfirmCategory removed — Unconfirm lives inside
  // the category detail page (AllocationBoard) now, next to the other
  // state controls. The dashboard only surfaces forward transitions.

  // ─── Engine settings helper (for category edit form) ───
  const updateEngineSettings = (setter, key, value) => {
    setter(prev => {
      const currentSettings = prev.settings || {};
      const currentEngine = currentSettings.engine || {};
      return { ...prev, settings: { ...currentSettings, engine: { ...currentEngine, [key]: value } } };
    });
  };

  if (loading) return <p className="text-gray-400 text-sm">{t('common.loading')}</p>;

  const selectedCat = selectedCatId ? categories.find(c => c.id === selectedCatId) : null;

  if (selectedCat) {
    // v0.50e-1d: per-category overrides removed. Staff access is governed
    // by a single `organise: "read" | "write" | null` for the whole board.
    const staffHasWrite = staffPerms && staffPerms['organise'] === 'write';
    const effectiveIsAdmin = isAdmin || staffHasWrite;

    return (
      <div>
        {/* Board header */}
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <button onClick={() => setSelectedCatId(null)}
              className="text-sm text-steel-blue hover:text-mid-navy inline-flex items-center gap-1">
              {t('organise.back')}
            </button>
            <h2 className="font-heading text-xl font-bold" style={{ color: 'var(--text-primary)' }}>{selectedCat.name}</h2>
            {/* v0.60e: removed the "one per person / several per person"
                badge that used to sit here. It was redundant (organiser
                already picked this category; the rule is set), and its
                `bg-gray-100 text-gray-400` styling rendered as a pale
                blob with poor contrast in dark mode. The same rule info
                still appears under each category tile on the category
                list view (line ~423 below), where it's contextually
                useful for comparing categories at a glance. */}
          </div>
          {isAdmin && (
            <div className="flex items-center gap-2">
              {/* v0.70d-3c-8: 'Edit group type' button removed —
                  editing now lives in the 'Manage group types' overview
                  in OrganiseDashboard. Per-category Auto-Zuordnung
                  settings still live in the gear popover here. Keeping
                  delete because it's a per-category destructive
                  action that's natural to perform from the detail
                  view. */}
              <button onClick={() => handleDeleteCat(selectedCat.id)}
                className="text-xs text-alert hover:opacity-80 border border-alert rounded-lg px-3 py-1.5">
                {t('organise.delete_group_type')}
              </button>
            </div>
          )}
        </div>

        {/* Edit category inline */}
        {/* v0.70d-3c-8: inline editingCat form removed —
            edit lives in the Einteilung overview now. */}

        <AllocationBoard
          eventId={eventId}
          eventName={eventName}
          category={selectedCat}
          allCategories={categories}
          onSelectCategory={setSelectedCatId}
          participantList={participantList}
          noteCounts={noteCounts}
          isAdmin={effectiveIsAdmin}
          marksPerm={staffPerms?.marks || ''}
          onDataChange={() => { loadCategories(); if (onDataChange) onDataChange(); }}
        />
        <ConfirmOverlay />
        <ToastHost />
      </div>
    );
  }

  // v50c-3c-2d: match AllocationBoard — include pending participants,
  // exclude only cancelled. Keeps totals aligned between the card stats
  // and the board's unassigned pool count.
  const totalParticipants = participantList.filter(p => p.registration_status !== 'cancelled').length;
  const ruleLabel = (rt) => rt === 'exclusive' ? t('organise.one_per_person') : t('organise.several_per_person');

  return (
    <div>
      {error && (() => {
        const { primary, detail } = formatErrorMessage(error, t);
        return (
          <ErrorBanner className="text-sm rounded-card p-3 mb-4">
            <p className="font-semibold">{primary}</p>
            {detail && <p className="text-xs opacity-70 mt-1">{detail}</p>}
          </ErrorBanner>
        );
      })()}

      <div className="flex items-center justify-between mb-4">
        <h2 className="font-heading text-xl font-bold" style={{ color: 'var(--text-primary)' }}>
          {t('organise.title')}
        </h2>
        {isAdmin && (
          <button onClick={() => { setManageOpen(o => !o); setEditingCat(null); }}
            className="text-xs font-semibold hover:underline flex items-center gap-1"
            style={{ color: 'var(--io-accent)' }}>
            <span style={{ display: 'inline-block', transform: manageOpen ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s' }}>▶</span>
            {t('organise.manage_group_types')}
          </button>
        )}
      </div>

      {/* ── Collapsible: Manage Group Types (v0.58c: extracted to GroupTypesEditor) ── */}
      {isAdmin && manageOpen && (
        <div
          className="rounded-2xl p-4 mb-6"
          style={{
            background: 'var(--app-bg)',
            border: '1px solid var(--card-border)',
          }}
        >
          <GroupTypesEditor
            eventId={eventId}
            isAdmin={isAdmin}
            onChange={() => { loadCategories(); if (onDataChange) onDataChange(); }}
          />
        </div>
      )}


      {categories.length === 0 ? (
        <div
          className="rounded-2xl p-12 text-center"
          style={{
            background: 'var(--app-bg)',
            border: '1px solid var(--card-border)',
            color: 'var(--text-subtle)',
          }}
        >
          <p className="text-sm">{t('organise.empty')}</p>
          <p className="text-xs mt-1">{t('organise.empty.hint')}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pb-4">
          {categories.map((cat, idx) => {
            const allocated = cat.allocated_count || 0;
            const unassigned = totalParticipants - allocated;
            const pct = totalParticipants > 0 ? Math.round((allocated / totalParticipants) * 100) : 0;
            const isDragOver = dragOverCatId === cat.id && dragCatId !== cat.id;
            const canMoveUp = idx > 0;
            const canMoveDown = idx < categories.length - 1;
            return (
              <div key={cat.id}
                draggable={isAdmin && HAS_FINE_POINTER}
                onDragStart={isAdmin && HAS_FINE_POINTER ? () => setDragCatId(cat.id) : undefined}
                onDragOver={isAdmin && HAS_FINE_POINTER ? (e) => { e.preventDefault(); setDragOverCatId(cat.id); } : undefined}
                onDragLeave={isAdmin && HAS_FINE_POINTER ? () => setDragOverCatId(null) : undefined}
                onDrop={isAdmin && HAS_FINE_POINTER ? (e) => { e.preventDefault(); handleReorderCats(dragCatId, cat.id); } : undefined}
                onClick={() => { if (!dragCatId) setSelectedCatId(cat.id); }}
                className={`card-surface-solid rounded-xl p-5 cursor-pointer hover:shadow-sm transition-all group select-none border-2 ${isDragOver ? 'border-steel-blue bg-steel-blue/5 scale-[1.01]' : 'border-transparent hover:border-steel-blue/40'}`}
                id={`cat-${cat.id}`}>
                {isAdmin && (
                  <div className="flex items-center justify-between gap-2 mb-2">
                    {/* Drag handle — pointer-fine devices only; hidden
                        visually until hover. v0.61c-2: gated on
                        HAS_FINE_POINTER so it doesn't surface on touch
                        devices via swipe-reveal or accidental hover-emulation. */}
                    {HAS_FINE_POINTER && (
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity cursor-grab active:cursor-grabbing">
                        <span className="text-gray-300 text-sm">⠿</span>
                        <span className="text-[9px] text-gray-300 uppercase tracking-wider">{t('common.drag_to_reorder')}</span>
                      </div>
                    )}
                    {/* Explicit reorder buttons — universal fallback for
                        touch devices where HTML5 DnD is flaky. Always visible. */}
                    <div className="flex items-center gap-0.5" onClick={e => e.stopPropagation()}>
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); if (canMoveUp) handleReorderCats(cat.id, categories[idx - 1].id); }}
                        disabled={!canMoveUp}
                        aria-label={t('common.move_earlier')}
                        title={t('common.move_earlier')}
                        className="w-6 h-6 rounded-md flex items-center justify-center text-xs hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed"
                        style={{ color: 'var(--text-subtle)' }}
                      >
                        ↑
                      </button>
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); if (canMoveDown) handleReorderCats(cat.id, categories[idx + 1].id); }}
                        disabled={!canMoveDown}
                        aria-label={t('common.move_later')}
                        title={t('common.move_later')}
                        className="w-6 h-6 rounded-md flex items-center justify-center text-xs hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed"
                        style={{ color: 'var(--text-subtle)' }}
                      >
                        ↓
                      </button>
                    </div>
                  </div>
                )}
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-heading font-bold text-lg text-body group-hover:text-steel-blue dark:group-hover:text-gold transition-colors">{cat.name}</h3>
                    <p className="text-[10px] text-gray-400 mt-0.5">
                      {ruleLabel(cat.rule_type)}
                      {cat.has_capacity && ' · ' + t('organise.capacity')}{cat.has_gender_restriction && ' · ' + t('organise.gender')}
                    </p>
                  </div>
                  <span className="text-xs font-semibold text-gray-400">{cat.unit_count} × {cat.item_label || 'Item'}</span>
                </div>
                <div className="mb-2">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span><span className="font-semibold text-body">{allocated}</span> {t('organise.assigned')}</span>
                    <span className="text-pending">{unassigned} {t('organise.unassigned')}</span>
                  </div>
                  <div className="w-full bg-gray-100 dark:bg-white/10 rounded-full h-2">
                    <div className="bg-steel-blue dark:bg-gold rounded-full h-2 transition-all" style={{ width: `${pct}%` }} />
                  </div>
                </div>
                <div className="flex flex-col gap-2 mt-1">
                  {/* v0.74a: per-category Auto-Allocate split-button removed
                      from the overview. Group-type overview is now pure
                      navigation — click into a group type to run the engine
                      from inside its allocation board. Removes overview/board
                      duplication of the same action. */}
                  {/* v50c-3c-2a: lifecycle CTA on the LEFT, pill on the RIGHT.
                      All left-bound (no ml-auto) so the card has a stable
                      left edge regardless of state transitions. Button before
                      pill matches the reading order: "do this action; current
                      state is X". */}
                  {(() => {
                    const state = deriveAllocState(cat);
                    const busy = confirmingCatId === cat.id;
                    return (
                      <div className="flex items-center gap-2 flex-wrap" onClick={e => e.stopPropagation()}>
                        {isAdmin && state === ALLOC_STATE.IN_PROGRESS && (
                          <button
                            onClick={(e) => handleConfirmCategory(cat.id, e)}
                            disabled={busy}
                            title={t('alloc.cta.confirm.hint')}
                            className="text-[10px] font-semibold px-2.5 py-1 rounded-md bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 disabled:opacity-50 whitespace-nowrap"
                          >
                            {busy ? t('alloc.cta.confirming') : t('alloc.cta.confirm')}
                          </button>
                        )}
                        {/* v0.50p: Unconfirm button removed from the dashboard
                            card. The same action now lives inside the
                            group-type detail (AllocationBoard) as a
                            "Confirmed · Unconfirm" banner at the top of the
                            stats card. The pill here still communicates
                            state at a glance; Unconfirm is one click away
                            (click the card → detail page → Unconfirm).
                            Aligns with the principle that the dashboard
                            surfaces primary/forward actions while detail
                            pages handle reversals. */}
                        <AllocStatusPill state={state} />
                      </div>
                    );
                  })()}
                </div>
              </div>
            );
          })}
        </div>
      )}
      <ConfirmOverlay />

      {/* v0.70d-1 R1 / v0.74a: OrganiseDashboard's legacy proposal
          modal was dead code (nothing called setProposal) AND the
          per-category Auto-Allocate split-button that fed
          setTriggerSuggestMode was removed in v0.74a. The real engine
          flow lives in AllocationBoard; this dashboard only routes
          users into it. If a future path ever needs a dashboard-level
          review it should import ReviewSurface rather than rebuild a
          modal. */}
      <ToastHost />
    </div>
  );
}
