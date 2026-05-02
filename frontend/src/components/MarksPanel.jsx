import { useState, useEffect, useMemo } from 'react';
import { marks as marksApi, events as eventsApi, participants as participantsApi } from '../services/api';
import { useConfirmOverlay } from './ConfirmOverlay';
import StrongDeleteConfirm from './StrongDeleteConfirm';
import { useI18n } from '../hooks/useI18n';
import EmptyState from './EmptyState';

import TranslatedError from './TranslatedError';
const PALETTE = [
  { colour: '#EF4444', label: 'Red' },
  { colour: '#F97316', label: 'Orange' },
  { colour: '#EAB308', label: 'Yellow' },
  { colour: '#22C55E', label: 'Green' },
  { colour: '#14B8A6', label: 'Teal' },
  { colour: '#3B82F6', label: 'Blue' },
  { colour: '#8B5CF6', label: 'Purple' },
  { colour: '#EC4899', label: 'Pink' },
  { colour: '#6B7280', label: 'Grey' },
];

// Colour conversion helpers
const hexToRgb = (hex) => {
  if (!hex) return null;
  const m = /^#?([0-9a-f]{6})$/i.exec(hex);
  if (!m) return null;
  const n = parseInt(m[1], 16);
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
};

const rgbToHex = (r, g, b) => {
  const clamp = (n) => Math.max(0, Math.min(255, parseInt(n, 10) || 0));
  return '#' + [clamp(r), clamp(g), clamp(b)].map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase();
};

const isValidHex = (s) => /^#[0-9A-Fa-f]{6}$/.test(s);

const VIEW_OPTION_KEYS = [
  { id: 'people', labelKey: 'marks.views.people' },
  { id: 'organise', labelKey: 'marks.views.organise' },
  { id: 'checkin', labelKey: 'marks.views.checkin' },
];

/**
 * MarksPanel (v0.50f)
 * ───────────────────
 * Authority rules:
 *   - Admin (isAdmin=true): full control — create, edit/delete any mark, import
 *   - Staff with marksPerm='write': create new marks; edit/delete only marks
 *     they created (matched by currentUserId against def.created_by_user_id)
 *   - Staff with marksPerm='read': read-only view of marks list
 *   - Anyone else: this panel shouldn't render (caller gates the route)
 *
 * Audit trail: each mark shows "Created by Alice" when the creator is known.
 * Marks without a creator (pre-v0.50f) render as unattributed ("System").
 *
 * Delete flow: uses StrongDeleteConfirm — type-to-confirm + shows
 * up-to-10 recently assigned participants so the destructive scope is
 * visible before proceeding.
 */
export default function MarksPanel({ eventId, isAdmin, currentUserId, marksPerm, embedded = false, onChange }) {
  const canWrite = isAdmin || marksPerm === 'write';
  const canImport = isAdmin; // admin-only; staff don't import marks in bulk

  const [defs, setDefs] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({ name: '', colour: '#EF4444', visible_in: ['people', 'organise', 'checkin'], cluster_behaviour: 'none' });
  const [colourDraft, setColourDraft] = useState('#EF4444');
  const [showImport, setShowImport] = useState(false);
  const [allEvents, setAllEvents] = useState([]);
  const [importEventId, setImportEventId] = useState('');
  const [error, setError] = useState(null);
  // v0.70d-3a-4 (M2): submitting flag for the create/edit submit
  // button. Mirror the saving-state pattern used by SetupCard
  // (uses `common.saving` for the in-flight label). MarksPanel was
  // missing this — submit button stayed as the static label
  // ("Add" / "Update") during the API call.
  const [submitting, setSubmitting] = useState(false);
  // Strong delete modal state
  const [deleteTarget, setDeleteTarget] = useState(null); // { id, name, colour }

  const { ConfirmOverlay } = useConfirmOverlay();
  const { t } = useI18n();
  const VIEW_OPTIONS = VIEW_OPTION_KEYS.map(v => ({ id: v.id, label: t(v.labelKey) }));

  // Can the current user modify a specific mark?
  // Admin → always yes. Staff write + creator match → yes. Else no.
  const canModify = (def) => {
    if (isAdmin) return true;
    if (marksPerm !== 'write') return false;
    return def.created_by_user_id && def.created_by_user_id === currentUserId;
  };

  // Participants by id for building the delete-dialog assignee list.
  const participantNameById = useMemo(() => {
    const m = {};
    participants.forEach(p => { m[p.id] = `${p.first_name || ''} ${p.last_name || ''}`.trim() || '—'; });
    return m;
  }, [participants]);

  // For the delete dialog: names of people this mark is assigned to,
  // sorted by recency (most recently assigned first). Limited to 10
  // rendered — StrongDeleteConfirm handles the "and N more" pill.
  const assigneesFor = (markId) => {
    const matches = assignments.filter(a => a.mark_id === markId);
    // assignments come back without a timestamp in the current API;
    // keep order as returned (treated as chronological) and reverse
    // so recent-first.
    const ordered = [...matches].reverse();
    const names = ordered
      .map(a => participantNameById[a.participant_id])
      .filter(Boolean);
    return { names, total: matches.length };
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { loadAll(); }, [eventId]);

  const loadAll = async () => {
    try {
      // v0.50f-1: creator name comes back on each mark from the backend
      // join — no separate users fetch needed, so this works for staff
      // who don't have user-management access.
      const [defsData, assignData, partsData] = await Promise.all([
        marksApi.listDefs(eventId),
        marksApi.listAssignments(eventId).catch(() => []),
        participantsApi.list(eventId).catch(() => []),
      ]);
      setDefs(defsData);
      setAssignments(assignData);
      setParticipants(partsData);
    } catch (err) { setError(err); }
    finally { setLoading(false); }
  };

  const loadDefs = async () => {
    // Kept for small reloads after create/edit/delete. Refreshes defs
    // + assignments (the frequently-changing pair). Users and
    // participants don't change from this panel's operations.
    try {
      const [d, a] = await Promise.all([
        marksApi.listDefs(eventId),
        marksApi.listAssignments(eventId).catch(() => []),
      ]);
      setDefs(d);
      setAssignments(a);
    } catch (err) { setError(err); }
  };

  const loadEvents = async () => {
    try {
      const data = await eventsApi.list();
      setAllEvents(data.filter(e => e.id !== eventId));
    } catch {}
  };

  const openImport = () => {
    setShowImport(true);
    loadEvents();
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    setSubmitting(true);
    try {
      await marksApi.createDef(eventId, form);
      setForm({ name: '', colour: '#EF4444', visible_in: ['people', 'organise', 'checkin'], cluster_behaviour: 'none' });
      setColourDraft('#EF4444');
      setShowCreate(false);
      await loadDefs();
      // v0.70d-2e-2 (M0): notify parent so SetupHub's marksDefs
      // length-driven `confirmed` prop reflects the change. Without
      // this the Marks card kept its yellow ✓ stripe even when the
      // last mark was deleted, because SetupHub's state was frozen
      // at initial-load.
      onChange?.();
    } catch (err) { setError(err); }
    finally { setSubmitting(false); }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await marksApi.updateDef(eventId, editingId, form);
      setEditingId(null);
      await loadDefs();
      onChange?.();
    } catch (err) { setError(err); }
    finally { setSubmitting(false); }
  };

  // v0.50f: deletion goes through StrongDeleteConfirm (type-to-confirm).
  // handleDelete opens the modal; handleDeleteConfirmed does the actual work
  // after the user has typed the name.
  const handleDelete = (def) => {
    setDeleteTarget(def);
  };

  const handleDeleteConfirmed = async () => {
    if (!deleteTarget) return;
    try {
      await marksApi.deleteDef(eventId, deleteTarget.id);
      setDeleteTarget(null);
      await loadDefs();
      onChange?.();
    } catch (err) {
      setError(err);
      setDeleteTarget(null);
    }
  };

  const startEdit = (def) => {
    setEditingId(def.id);
    setForm({ name: def.name, colour: def.colour, visible_in: def.visible_in || [], cluster_behaviour: def.cluster_behaviour || 'none' });
    setColourDraft(def.colour);
    setShowCreate(false);
  };

  const handleImport = async () => {
    if (!importEventId) return;
    try {
      await marksApi.importFrom(eventId, importEventId);
      setShowImport(false);
      setImportEventId('');
      await loadDefs();
      onChange?.();
    } catch (err) { setError(err); }
  };

  if (loading) return <p className="text-gray-400 text-sm">{t('common.loading')}</p>;

  // Render form JSX inline — NOT as a nested component (would cause remount on every keystroke)
  const renderForm = (onSubmit, submitLabel) => {
    const rgb = hexToRgb(form.colour) || { r: 0, g: 0, b: 0 };
    const updateRgb = (key, value) => {
      const next = { ...rgb, [key]: Math.max(0, Math.min(255, parseInt(value, 10) || 0)) };
      const newHex = rgbToHex(next.r, next.g, next.b);
      setForm(p => ({ ...p, colour: newHex }));
      setColourDraft(newHex);
    };
    // v0.50d-5b: theme-aware input style reused across the form.
    const inputStyle = {
      background: 'var(--app-bg)',
      borderColor: 'var(--card-border)',
      color: 'var(--text-primary)',
    };
    const inputBase = "rounded-card focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)] border";
    return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div>
        <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
          style={{ color: 'var(--text-subtle)' }}>
          {t('marks.new.name_label')}
        </label>
        <input type="text" placeholder={t('marks.new.name')} value={form.name}
          onChange={e => setForm(p => ({ ...p, name: e.target.value }))} required autoFocus
          className={`w-full ${inputBase} px-3 py-2 text-sm`} style={inputStyle} />
      </div>
      <div>
        <label className="block text-[10px] uppercase tracking-caps font-semibold mb-2"
          style={{ color: 'var(--text-subtle)' }}>
          {t('marks.new.colour')}
        </label>
        {/* Quick palette — mark colours are user-facing category colours, keep bright */}
        <div className="flex gap-2 flex-wrap mb-2.5">
          {PALETTE.map(({ colour, label }) => (
            <button key={colour} type="button" title={label}
              onClick={() => { setForm(p => ({ ...p, colour })); setColourDraft(colour); }}
              className={`w-6 h-6 rounded-full border-2 transition-all ${
                form.colour === colour ? 'scale-110' : ''
              }`}
              style={{
                backgroundColor: colour,
                borderColor: form.colour === colour ? 'var(--text-primary)' : 'transparent',
              }} />
          ))}
        </div>
        {/* Custom: native picker + hex + RGB */}
        <div
          className="flex items-center gap-3 flex-wrap rounded-card p-2"
          style={{ background: 'var(--app-bg)', border: '1px solid var(--card-border)' }}
        >
          <input type="color" value={isValidHex(form.colour) ? form.colour : '#EF4444'}
            onChange={e => { const v = e.target.value.toUpperCase(); setForm(p => ({ ...p, colour: v })); setColourDraft(v); }}
            className="w-9 h-9 rounded-card cursor-pointer p-0.5"
            style={{ background: 'transparent', border: '1px solid var(--card-border)' }}
            title={t('marks.colour_picker')} />
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] font-semibold" style={{ color: 'var(--text-subtle)' }}>
              {t('marks.colour_hex')}
            </span>
            <input type="text" value={colourDraft} maxLength={7}
              onChange={e => {
                let v = e.target.value;
                if (v && !v.startsWith('#')) v = '#' + v;
                v = v.toUpperCase();
                setColourDraft(v);
                if (isValidHex(v)) setForm(p => ({ ...p, colour: v }));
              }}
              onBlur={() => { if (!isValidHex(colourDraft)) setColourDraft(form.colour); }}
              placeholder="#RRGGBB"
              className={`w-20 ${inputBase} px-2 py-1 text-xs font-mono`} style={inputStyle} />
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] font-semibold" style={{ color: 'var(--text-subtle)' }}>
              {t('marks.colour_rgb')}
            </span>
            {['r', 'g', 'b'].map(k => (
              <input key={k} type="number" min={0} max={255} value={rgb[k]}
                onChange={e => updateRgb(k, e.target.value)}
                className={`w-12 ${inputBase} px-1 py-1 text-[11px] text-center`} style={inputStyle} />
            ))}
          </div>
        </div>
      </div>
      <div>
        <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1.5"
          style={{ color: 'var(--text-subtle)' }}>
          {t('marks.new.visible_in')}
        </label>
        <div className="flex gap-4 flex-wrap">
          {VIEW_OPTIONS.map(v => (
            <label key={v.id} className="flex items-center gap-1.5 text-xs cursor-pointer"
              style={{ color: 'var(--text-muted)' }}>
              <input type="checkbox" checked={(form.visible_in || []).includes(v.id)}
                onChange={() => setForm(prev => {
                  const arr = prev.visible_in || [];
                  return { ...prev, visible_in: arr.includes(v.id) ? arr.filter(x => x !== v.id) : [...arr, v.id] };
                })}
                className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold" />
              {v.label}
            </label>
          ))}
        </div>
      </div>
      {/* v1.0-pre #23: cluster_behaviour UI removed. Behaviour now lives
          per-category in the engine settings popover (next to Auto-Allocate),
          alongside the mark priorities list. The MarkDefinition.cluster_behaviour
          column on the model stays for backward compatibility — old categories
          that haven't yet been re-saved with the new shape still read the
          global default. */}
      <div className="flex items-center gap-2">
        <button type="submit" disabled={submitting}
          className="text-xs font-semibold px-4 py-2 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 disabled:opacity-50">
          {submitting ? t('common.saving') : submitLabel}
        </button>
        <button type="button" onClick={() => { setShowCreate(false); setEditingId(null); }}
          className="text-xs font-medium px-2 py-2 hover:underline"
          style={{ color: 'var(--text-subtle)' }}>
          {t('common.cancel')}
        </button>
      </div>
    </form>
    );
  };

  return (
    <div>
      {/* Header row — skipped entirely in embedded mode (SetupCard provides header) */}
      {(!embedded || canWrite) && (
        <div className="flex items-center justify-between mb-4">
          {embedded ? (
            <div />
          ) : (
            <div>
              <h3 className="font-heading font-bold" style={{ color: 'var(--text-primary)' }}>
                {t('marks.title')}
              </h3>
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                {t('marks.subtitle')}
              </p>
            </div>
          )}
          {canWrite && (
            <div className="flex items-center gap-3">
              {canImport && (
                <button onClick={openImport}
                  className="text-xs font-medium px-3 py-1.5 rounded-card border hover:bg-black/5 dark:hover:bg-white/10"
                  style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}>
                  {t('marks.import')}
                </button>
              )}
              <button onClick={() => { setShowCreate(!showCreate); setEditingId(null); }}
                className="text-xs font-semibold hover:underline"
                style={{ color: 'var(--io-accent)' }}>
                {showCreate ? t('common.cancel') : t('marks.add')}
              </button>
            </div>
          )}
        </div>
      )}

      <TranslatedError err={error} className="text-xs rounded-card p-3 mb-3" />

      {/* v0.58e-2: persistent allocation-context hint in embedded mode.
          Explains why marks matter BEYOND just labelling, since once the
          first mark exists the SetupCard switches from emptyCopy to a
          count summary and the "why" context disappears. */}
      {embedded && (
        <p className="text-xs mb-3" style={{ color: 'var(--text-subtle)' }}>
          {t('marks.allocation_hint')}
        </p>
      )}

      {/* Import panel */}
      {showImport && (
        <div
          className="card-surface-solid rounded-2xl p-4 mb-4"
          style={{ border: '1px solid var(--card-border)' }}
        >
          <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>{t('marks.import.hint')}</p>
          <div className="flex gap-2 flex-wrap">
            <select value={importEventId} onChange={e => setImportEventId(e.target.value)}
              className="flex-1 min-w-[200px] rounded-card border focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)] px-3 py-2 text-sm"
              style={{
                background: 'var(--app-bg)',
                borderColor: 'var(--card-border)',
                color: 'var(--text-primary)',
              }}>
              <option value="">{t('marks.select_event')}</option>
              {allEvents.map(e => <option key={e.id} value={e.id}>{e.name}</option>)}
            </select>
            <button onClick={handleImport} disabled={!importEventId}
              className="text-xs font-semibold px-4 py-2 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 disabled:opacity-50">
              {t('marks.import.submit')}
            </button>
            <button onClick={() => setShowImport(false)}
              className="text-xs font-medium px-2 py-2 hover:underline"
              style={{ color: 'var(--text-subtle)' }}>
              {t('common.cancel')}
            </button>
          </div>
        </div>
      )}

      {/* Create form */}
      {showCreate && (
        <div
          className="card-surface-solid rounded-2xl p-4 mb-4"
          style={{ border: '1px solid var(--card-border)' }}
        >
          {renderForm(handleCreate, t('marks.new.submit'))}
        </div>
      )}

      {/* List */}
      {defs.length === 0 && !showCreate ? (
        <EmptyState
          compact
          title={t('marks.empty.title')}
          hint={embedded ? null : (t('marks.empty.hint'))}
        />
      ) : (
        <div className="space-y-2">
          {defs.map(def => (
            <div key={def.id}>
              {editingId === def.id ? (
                <div
                  className="card-surface-solid rounded-2xl p-4"
                  style={{
                    borderTop: '1px solid var(--card-border)',
                    borderRight: '1px solid var(--card-border)',
                    borderBottom: '1px solid var(--card-border)',
                    borderLeft: '3px solid var(--io-accent)',
                  }}
                >
                  <p className="text-xs font-semibold mb-3" style={{ color: 'var(--io-accent)' }}>
                    {t('organise.editing', { name: def.name })}
                  </p>
                  {renderForm(handleUpdate, t('common.save'))}
                </div>
              ) : (
                <div className="card-surface-solid rounded-2xl px-4 py-3 flex items-center gap-3"
                  style={{ border: '1px solid var(--card-border)' }}>
                  <span className="w-4 h-4 rounded-full shrink-0" style={{ backgroundColor: def.colour }} />
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
                      <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{def.name}</span>
                      <span className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>
                        {(def.visible_in || []).map(v => VIEW_OPTIONS.find(x => x.id === v)?.label).filter(Boolean).join(', ') || t('marks.hidden_everywhere')}
                      </span>
                    </div>
                    <p className="text-[10px] mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                      {def.created_by_name
                        ? t('marks.created_by', { name: def.created_by_name })
                        : (def.created_by_user_id
                            ? t('marks.created_by', { name: t('marks.unknown_user') })
                            : t('marks.created_by_system'))}
                    </p>
                  </div>
                  {canModify(def) && (
                    <div className="flex gap-3 shrink-0">
                      <button onClick={() => startEdit(def)}
                        className="text-[10px] font-semibold hover:underline"
                        style={{ color: 'var(--io-accent)' }}>
                        {t('common.edit')}
                      </button>
                      <button onClick={() => handleDelete(def)}
                        className="text-[10px] font-semibold hover:underline"
                        style={{ color: 'var(--alert-burgundy)' }}>
                        {t('common.delete')}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      {deleteTarget && (() => {
        const { names, total } = assigneesFor(deleteTarget.id);
        return (
          <StrongDeleteConfirm
            open={true}
            title={t('marks.delete.strong_title')}
            itemLabel={t('marks.delete.item_label')}
            itemName={deleteTarget.name}
            itemColour={deleteTarget.colour}
            assigneeCount={total}
            assigneeNames={names}
            warning={t('marks.delete.strong_warning')}
            onConfirm={handleDeleteConfirmed}
            onCancel={() => setDeleteTarget(null)}
          />
        );
      })()}
      <ConfirmOverlay />
    </div>
  );
}
