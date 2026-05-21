import { useState, useEffect, useCallback } from 'react';
import { allocationCategories } from '../services/api';
import { useConfirmOverlay } from './ConfirmOverlay';
import { useI18n } from '../hooks/useI18n';
import TranslatedError from './TranslatedError';

// v0.61c-1: detect a pointer device with a fine-grained pointer (mouse,
// trackpad). Touch-only devices report `coarse` and report `pointer:
// none` for hover-driven interactions. We use this to gate drag-to-
// reorder, which is a desktop affordance — touch devices use the
// ▲▼ arrows. Reading at module scope (not on every render) is fine
// because pointer capability doesn't change mid-session in any
// realistic way; viewport width does (rotate), pointer-fine doesn't
// (you don't suddenly grow a mouse).
const HAS_FINE_POINTER = typeof window !== 'undefined'
  && typeof window.matchMedia === 'function'
  && window.matchMedia('(hover: hover) and (pointer: fine)').matches;

/**
 * GroupTypesEditor — standalone manage UI for allocation categories.
 *
 * Extracted from OrganiseDashboard (v0.58c) so the same component can be
 * used from two surfaces:
 *   - Setup phase (`SetupHub` group_types card) — where there are no
 *     participants yet and showing a board would be misleading.
 *   - Event phase (`OrganiseDashboard` collapsible "Manage Group Types"
 *     section) — same editor, wrapped in a collapsible on the board.
 *
 * Self-contained: owns its own categories state, its own editingCat
 * (not shared with the parent's board-side editingCat), and its own
 * confirm overlay. Calls `onChange` after every successful mutation
 * so parents can refresh their derived state (grid, summary text).
 *
 * Props:
 *   eventId  — required
 *   isAdmin  — required; renders nothing if false (non-admins can't edit)
 *   onChange — optional callback; fired after create/update/delete
 */
export default function GroupTypesEditor({ eventId, isAdmin, onChange }) {
  const [categories, setCategories] = useState([]);
  const [editingCat, setEditingCat] = useState(null);
  const [showAddCat, setShowAddCat] = useState(false);
  const [newCat, setNewCat] = useState({
    name: '',
    item_label: '',
    rule_type: 'exclusive',
    has_capacity: false,
    has_gender_restriction: false,  // v0.74: deprecated, default false
    exclusive_group_codes: false,  // v0.74
  });
  const [error, setError] = useState(null);
  // v0.61c-1: drag-to-reorder gating now uses HAS_FINE_POINTER (mouse/
  // trackpad detection) instead of the JS-state `isDesktop` viewport
  // check, which fired true on landscape mobile and on phones with
  // viewport ≥768 CSS px — the grip ⠿ then surfaced when users
  // swiped a row sideways. Pointer-fine is a more honest predicate
  // for "user can drag" than viewport width. Only `dragId` state
  // remains — needed to visually fade the row being dragged.
  const [dragId, setDragId] = useState(null);
  const { confirm, ConfirmOverlay } = useConfirmOverlay();
  const { t } = useI18n();

  const loadCategories = useCallback(async () => {
    try {
      const data = await allocationCategories.list(eventId);
      setCategories(data);
      setError(null);
    } catch (err) { setError(err); }
  }, [eventId]);

  useEffect(() => { loadCategories(); }, [loadCategories]);

  const notifyChange = () => { if (onChange) onChange(); };

  const handleCreateCat = async (e) => {
    e.preventDefault();
    if (!newCat.name.trim()) return;
    try {
      await allocationCategories.create(eventId, newCat);
      setNewCat({ name: '', item_label: '', rule_type: 'exclusive', has_capacity: false, has_gender_restriction: false, exclusive_group_codes: false });
      setShowAddCat(false);
      await loadCategories();
      notifyChange();
    } catch (err) { setError(err); }
  };

  const handleUpdateCat = async (e) => {
    e.preventDefault();
    if (!editingCat) return;
    // v0.74: pre-v0.74 Bug 3 wipe-on-toggle-off ceremony is removed.
    // Capacity is required-everywhere in v0.74; toggling has_capacity
    // off no longer wipes unit data — it just signals the engine to
    // ignore the caps. Data stays intact.
    try {
      await allocationCategories.update(eventId, editingCat.id, editingCat);
      setEditingCat(null);
      await loadCategories();
      notifyChange();
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
      await loadCategories();
      notifyChange();
    } catch (err) { setError(err); }
  };

  // v0.58e-1: Reorder up/down — works on both mobile and desktop.
  // On mobile, the category-grid drag-to-reorder on the board is disabled
  // (to keep scroll working), so these buttons are the only reorder path
  // on phones. On desktop both work and either is fine.
  const handleReorder = async (fromIdx, toIdx) => {
    if (toIdx < 0 || toIdx >= categories.length) return;
    const reordered = [...categories];
    const [moved] = reordered.splice(fromIdx, 1);
    reordered.splice(toIdx, 0, moved);
    setCategories(reordered);
    try {
      await allocationCategories.reorder(eventId, reordered.map(c => c.id));
      notifyChange();
    } catch {
      loadCategories();
    }
  };

  const ruleLabel = (rt) => rt === 'exclusive' ? t('organise.one_per_person') : t('organise.several_per_person');

  if (!isAdmin) return null;

  return (
    <div className="space-y-3">
      <TranslatedError err={error} className="text-sm rounded-card p-3" />

      {/* Existing categories list */}
      {categories.length > 0 && (
        <div className="space-y-1.5">
          {categories.map((cat, idx) => (
            <div key={cat.id}>
              {editingCat?.id === cat.id ? (
                <div
                  className="card-surface-solid rounded-card p-3"
                  style={{
                    borderTop: '1px solid var(--card-border)',
                    borderRight: '1px solid var(--card-border)',
                    borderBottom: '1px solid var(--card-border)',
                    borderLeft: '3px solid var(--io-accent)',
                  }}
                >
                  <form onSubmit={handleUpdateCat} className="space-y-2">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold" style={{ color: 'var(--io-accent)' }}>
                        {t('organise.editing', { name: editingCat.name })}
                      </span>
                      <button type="button" onClick={() => setEditingCat(null)}
                        className="text-xs hover:underline"
                        style={{ color: 'var(--text-subtle)' }}>
                        {t('common.cancel')}
                      </button>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      <div>
                        <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
                          style={{ color: 'var(--text-subtle)' }}>
                          {t('common.name')}
                        </label>
                        <input type="text" value={editingCat.name}
                          onChange={e => setEditingCat(p => ({ ...p, name: e.target.value }))}
                          className="w-full rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]" />
                      </div>
                      <div>
                        <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
                          style={{ color: 'var(--text-subtle)' }}>
                          {t('organise.item_label')}
                          <span className="font-normal ml-1 normal-case" style={{ color: 'var(--text-subtle)', letterSpacing: 'normal' }}>
                            {t('organise.item_label.hint')}
                          </span>
                        </label>
                        <input type="text" placeholder="e.g. Room, Team, Session" value={editingCat.item_label || ''}
                          onChange={e => setEditingCat(p => ({ ...p, item_label: e.target.value }))}
                          className="w-full rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]" />
                      </div>
                    </div>
                    <div>
                      <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
                        style={{ color: 'var(--text-subtle)' }}>
                        {t('organise.rule_type.question')}
                      </label>
                      <select value={editingCat.rule_type}
                        onChange={e => setEditingCat(p => ({ ...p, rule_type: e.target.value }))}
                        className="rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]">
                        <option value="exclusive">{t('organise.rule.exclusive')}</option>
                        <option value="overlapping">{t('organise.rule.overlapping')}</option>
                      </select>
                    </div>
                    <div className="flex gap-4 flex-wrap">
                      <label className="flex items-center gap-1.5 text-xs cursor-pointer"
                        style={{ color: 'var(--text-muted)' }}>
                        <input type="checkbox" checked={!!editingCat.has_capacity}
                          onChange={e => setEditingCat(p => ({ ...p, has_capacity: e.target.checked }))}
                          className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold" />
                        {t('organise.capacity_limits')}
                      </label>
                      {/* v1.0-pre #24: "Group codes claim units exclusively"
                          checkbox removed from this group-type editor — it
                          now lives in the per-category Engine settings panel
                          (next to Auto-Allocate), where the rest of the
                          allocation behaviour is configured. The field stays
                          on the category record for API compat; existing
                          values are honoured. */}
                      {/* v0.74: has_gender_restriction toggle deprecated. Engine
                          reads unit-level gender_restriction directly. The
                          checkbox is removed from the UI. The DB column stays
                          for backward compat, to be dropped at v1.0 cut. */}
                    </div>
                    <button type="submit"
                      className="text-xs font-semibold px-3 py-1.5 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80">
                      {t('common.save')}
                    </button>
                  </form>
                </div>
              ) : (
                <div
                  className="card-surface-solid flex items-center justify-between rounded-card px-3 py-2"
                  draggable={HAS_FINE_POINTER}
                  onDragStart={() => setDragId(cat.id)}
                  onDragOver={e => { if (dragId && dragId !== cat.id) e.preventDefault(); }}
                  onDrop={() => {
                    if (!dragId || dragId === cat.id) { setDragId(null); return; }
                    const fromIdx = categories.findIndex(c => c.id === dragId);
                    if (fromIdx !== -1) handleReorder(fromIdx, idx);
                    setDragId(null);
                  }}
                  onDragEnd={() => setDragId(null)}
                  style={{
                    border: '1px solid var(--card-border)',
                    cursor: HAS_FINE_POINTER ? 'move' : undefined,
                    opacity: dragId === cat.id ? 0.4 : 1,
                  }}
                >
                  <div className="min-w-0 flex items-center gap-2">
                    {/* v0.61c-1: grip — only rendered on devices with a
                        fine-grained pointer (mouse/trackpad). Touch users
                        continue with the ▲▼ arrows below. Previously this
                        was JS-gated on viewport width and surfaced on
                        landscape mobile when users swiped a row. */}
                    {HAS_FINE_POINTER && (
                      <span className="text-[10px] select-none"
                        style={{ color: 'var(--text-subtle)', opacity: 0.4 }}
                        aria-hidden="true">
                        ⠿
                      </span>
                    )}
                    <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{cat.name}</span>
                    <span className="text-[10px] ml-2" style={{ color: 'var(--text-subtle)' }}>
                      {ruleLabel(cat.rule_type)}
                    </span>
                  </div>
                  <div className="flex gap-2 items-center shrink-0">
                    {/* v0.58e-1: reorder arrows — universal on mobile + desktop */}
                    <button
                      onClick={() => handleReorder(idx, idx - 1)}
                      disabled={idx === 0}
                      aria-label={t('organise.move_up')}
                      title={t('organise.move_up')}
                      className="text-sm leading-none px-1 disabled:opacity-20 hover:opacity-70"
                      style={{ color: 'var(--text-subtle)' }}>
                      ▲
                    </button>
                    <button
                      onClick={() => handleReorder(idx, idx + 1)}
                      disabled={idx === categories.length - 1}
                      aria-label={t('organise.move_down')}
                      title={t('organise.move_down')}
                      className="text-sm leading-none px-1 disabled:opacity-20 hover:opacity-70"
                      style={{ color: 'var(--text-subtle)' }}>
                      ▼
                    </button>
                    <button onClick={() => setEditingCat({ ...cat })}
                      className="text-[10px] font-semibold hover:underline ml-1"
                      style={{ color: 'var(--io-accent)' }}>
                      {t('common.edit')}
                    </button>
                    <button onClick={() => handleDeleteCat(cat.id)}
                      className="text-[10px] font-semibold hover:underline"
                      style={{ color: 'var(--alert-burgundy)' }}>
                      {t('common.delete')}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Add new category */}
      {!showAddCat ? (
        <button onClick={() => setShowAddCat(true)}
          className="text-xs font-semibold hover:underline"
          style={{ color: 'var(--io-accent)' }}>
          + {t('organise.add_group_type')}
        </button>
      ) : (
        <div
          className="card-surface-solid rounded-card p-3"
          style={{ border: '1px solid var(--card-border)' }}
        >
          <form onSubmit={handleCreateCat} className="space-y-2">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>
                {t('organise.add_group_type')}
              </span>
              <button type="button" onClick={() => setShowAddCat(false)}
                className="text-xs hover:underline"
                style={{ color: 'var(--text-subtle)' }}>
                {t('common.cancel')}
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <div>
                <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
                  style={{ color: 'var(--text-subtle)' }}>
                  {t('common.name')}
                </label>
                <input type="text" placeholder={t('organise.group_type_name_placeholder')} value={newCat.name}
                  onChange={e => setNewCat(p => ({ ...p, name: e.target.value }))} required
                  className="w-full rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]" />
              </div>
              <div>
                <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
                  style={{ color: 'var(--text-subtle)' }}>
                  {t('organise.item_label')}
                  <span className="font-normal ml-1 normal-case" style={{ color: 'var(--text-subtle)', letterSpacing: 'normal' }}>
                    {t('organise.item_label.hint')}
                  </span>
                </label>
                <input type="text" placeholder="e.g. Room, Team" value={newCat.item_label}
                  onChange={e => setNewCat(p => ({ ...p, item_label: e.target.value }))}
                  className="w-full rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]" />
              </div>
            </div>
            <div className="flex flex-wrap gap-3 items-end">
              <div>
                <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
                  style={{ color: 'var(--text-subtle)' }}>
                  {t('organise.rule_type.question')}
                </label>
                <select value={newCat.rule_type}
                  onChange={e => setNewCat(p => ({ ...p, rule_type: e.target.value }))}
                  className="rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]">
                  <option value="exclusive">{t('organise.rule.exclusive_eg')}</option>
                  <option value="overlapping">{t('organise.rule.overlapping')}</option>
                </select>
              </div>
              <label className="flex items-center gap-1.5 text-xs cursor-pointer"
                style={{ color: 'var(--text-muted)' }}>
                <input type="checkbox" checked={newCat.has_capacity}
                  onChange={e => setNewCat(p => ({ ...p, has_capacity: e.target.checked }))}
                  className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold" />
                {t('organise.capacity_limits')}
              </label>
              {/* v1.0.0k: leftover has_gender_restriction toggle removed
                  from Create form to match Edit form. The v0.74
                  deprecation only ever removed it from Edit; this
                  finishes the job. Gender separation lives at the unit
                  level (per-room gender_restriction column) and is the
                  field the engine actually reads. The category-level
                  column stays in the DB for backward compat, defaults
                  to false on new categories, and is scheduled to be
                  dropped in a future migration. */}
              <button type="submit"
                className="text-xs font-semibold px-4 py-1.5 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80">
                {t('common.create')}
              </button>
            </div>
          </form>
        </div>
      )}

      <ConfirmOverlay />
    </div>
  );
}
