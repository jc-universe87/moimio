import { useState, useEffect, useMemo, useRef } from 'react';
import { participants as participantsApi, checkin as checkinApi, customFields as cfApi } from '../services/api';
import { useDateFormat } from '../hooks/useDateFormat';
import { useConfirmOverlay } from './ConfirmOverlay';
import MarkDots from './MarkDots';
import MarkAssignModal from './MarkAssignModal';
import { useMarks } from '../hooks/useMarks';
import { useI18n } from '../hooks/useI18n';
import EmptyState from './EmptyState';
import InsightPanel from './InsightPanel';
import TranslatedError from './TranslatedError';
import { useEventStream } from '../hooks/useEventStream';

// Built-in registration fields that can appear as read-only display columns.
// v0.50e-1d: group_code moved here from the fixed-columns list. It's now a
// toggleable column defaulting OFF — small churches typically don't use
// group codes, and having it always on was clutter. Staff can re-enable it
// via the Columns picker if needed.
const REG_DISPLAY_COLS = [
  { id: 'reg_group_code', label: 'checkin.group_code', field: 'group_code', render: (p) => p.group_code ? <span className="font-mono text-xs bg-gray-100 dark:bg-white/10 dark:text-off-white px-1 py-0.5 rounded">{p.group_code}</span> : '—' },
  { id: 'reg_gender', label: 'people.col.gender', field: 'gender', render: null },
  { id: 'reg_phone', label: 'people.col.phone', field: 'phone', render: (p) => p.phone || '—' },
  { id: 'reg_church', label: 'people.col.church', field: 'church_organisation', render: (p) => p.church_organisation || '—' },
  { id: 'reg_country', label: 'people.col.country', field: 'country', render: (p) => p.country || '—' },
  { id: 'reg_address', label: 'people.col.address', field: 'address', render: (p) => p.address || '—' },
  { id: 'reg_dob', label: 'people.col.dob', field: 'date_of_birth', render: null }, // uses formatDate
  { id: 'reg_message', label: 'people.col.message', field: 'message', render: (p) => p.message || '—' },
  { id: 'reg_registered_at', label: 'people.col.registered_at', field: null, render: (p) => p.created_at ? new Date(p.created_at).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' }) : '—' },
  { id: 'reg_checkin_at', label: 'checkin.col.checkin_time', field: null, render: (p) => p.checked_in_at ? new Date(p.checked_in_at).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' }) : '—' },
];

export default function CheckInPanel({ eventId, userId, participantList, isAdmin, canCreateColumns, canViewColumns, marksPerm, noteCounts, onOpenNotes }) {
  // v0.50f-1: mark modal opens for everyone (read is implicit — clicking a
  // mark dot shows what marks mean). Only canAssign is gated by marksPerm.
  // isAdmin bypasses.
  const canAssignMarks = isAdmin || marksPerm === 'write';
  const [tickFields, setTickFields] = useState([]);   // custom tick-off columns
  const [values, setValues] = useState({});
  const [customFieldDefs, setCustomFieldDefs] = useState([]); // custom registration fields
  const [search, setSearch] = useState('');
  const [checkinFilter, setCheckinFilter] = useState(''); // '' | 'checked_in' | 'not_checked_in'
  const [newFieldName, setNewFieldName] = useState('');
  const [showCreateField, setShowCreateField] = useState(false);
  const [showColPicker, setShowColPicker] = useState(false);
  const [colPickerPos, setColPickerPos] = useState({ top: 0, right: 0 });
  // v0.58g: Which mobile cards have their "details" (reg + cf pills) expanded.
  // Set of participant ids. Defaults empty → collapsed for all, so the
  // first-mobile-glance screen only shows hot-path work (name + ✓ + tick pills).
  // v0.61c: persisted to localStorage per (userId, eventId) so the
  // expanded state survives reload — same scoping as the existing
  // ciKey for column visibility. Stored as a JSON array of IDs;
  // missing entries are inert if a participant gets deleted.
  const expandedStorageKey = eventId && userId ? `moimio_ci_expanded_${userId}_${eventId}` : null;
  const [mobileExpandedIds, setMobileExpandedIds] = useState(() => {
    if (expandedStorageKey) {
      try {
        const saved = localStorage.getItem(expandedStorageKey);
        if (saved) return new Set(JSON.parse(saved));
      } catch {}
    }
    return new Set();
  });
  const toggleMobileExpanded = (pid) => setMobileExpandedIds(prev => {
    const next = new Set(prev);
    if (next.has(pid)) next.delete(pid); else next.add(pid);
    if (expandedStorageKey) {
      try { localStorage.setItem(expandedStorageKey, JSON.stringify([...next])); } catch {}
    }
    return next;
  });
  // v0.61a: InsightPanel wiring — ⓘ button opens the same slide-out panel
  // used in the Organise board. v1.0-pre: now wired to both the mobile-card
  // and the desktop-table layouts so the same shortcut works on every
  // viewport. The panel itself works on both viewports.
  const [insightParticipant, setInsightParticipant] = useState(null);

  // localStorage helpers — defined before useState so they can be used in initialisers
  const ciKey = eventId && userId ? `moimio_ci_cols_${userId}_${eventId}` : null;
  const ciOrderKey = eventId && userId ? `moimio_ci_col_order_${userId}_${eventId}` : null;
  const getCiSaved = () => {
    if (!ciKey) return {};
    try { return JSON.parse(localStorage.getItem(ciKey) || '{}'); } catch { return {}; }
  };
  const saveCiCols = (patch) => {
    if (!ciKey) return;
    try { localStorage.setItem(ciKey, JSON.stringify({ ...getCiSaved(), ...patch })); } catch {}
  };

  const _ci = getCiSaved();
  // v0.50e-1a: on first visit (no saved state), default Check-In Time on.
  // Check-In tick column + Name + No. are always visible (they're not in this
  // optional list). Once the user saves a column state, regCols is an array
  // (possibly empty) and we respect it exactly.
  const DEFAULT_REG_COLS = ['reg_checkin_at'];
  const [visibleRegCols, setVisibleRegCols] = useState(
    new Set(Array.isArray(_ci.regCols) ? _ci.regCols : DEFAULT_REG_COLS)
  );
  const [visibleTickCols, setVisibleTickCols] = useState(new Set()); // populated in loadAll
  // v0.50e-1a: cfCols defaults set in loadAll() once we know which custom
  // fields are boolean ('tick') fields — those default on, others default off.
  const [visibleCfCols, setVisibleCfCols] = useState(new Set(Array.isArray(_ci.cfCols) ? _ci.cfCols : []));
  const [showNotes, setShowNotes] = useState(!!_ci.showNotes);
  const [colOrder, setColOrder] = useState(() => {
    if (ciOrderKey) { try { const s = localStorage.getItem(ciOrderKey); if (s) return JSON.parse(s); } catch {} }
    return [];
  });
  const [dragColId, setDragColId] = useState(null);
  const [sortCol, setSortCol] = useState('participant_number');
  const [sortDir, setSortDir] = useState('asc');
  const handleSort = (col) => {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortCol(col); setSortDir('asc'); }
  };
  const sortArrow = (col) => {
    if (sortCol !== col) return <span className="text-subtle ml-0.5">↕</span>;
    return <span className="text-steel-blue ml-0.5">{sortDir === 'asc' ? '↑' : '↓'}</span>;
  };
  const [markModal, setMarkModal] = useState(null);
  const { defs: markDefs, assignments: markAssignments, getParticipantMarks, assign: assignMark, unassign: unassignMark } = useMarks(eventId);
  const colPickerBtnRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  // v0.70d-2e-4 (C2): the per-category allocation-status banner
  // was removed; the related state + load effect for it were
  // removed too. The top-of-panel progress indicator below the
  // search bar uses checkedInCount + activeParticipantList.length
  // directly, no separate fetch needed.
  const { formatDate } = useDateFormat();
  const { t } = useI18n();
  const colLabel = (label) => label.includes('.') ? t(label) : label;
  const { confirm, ConfirmOverlay } = useConfirmOverlay();

  useEffect(() => { loadAll(); }, [eventId]);

  const loadAll = async () => {
    try {
      const [f, v, cf] = await Promise.all([
        checkinApi.listFields(eventId),
        checkinApi.getValues(eventId),
        cfApi.list(eventId),
      ]);
      setTickFields(f);
      setValues(v);
      setCustomFieldDefs(cf);
      // Restore saved tick cols, or default to all visible
      const saved = getCiSaved();
      setVisibleTickCols(saved.tickCols ? new Set(saved.tickCols) : new Set(f.map(x => x.id)));
      // v0.50e-1a: default custom-field columns — if no saved state, default
      // to boolean custom fields (they're the "admin-created tick columns"
      // per §check-in defaults). Other types default off; user opts in via
      // the Columns pill. Once saved, cfCols is an array we respect verbatim.
      if (!Array.isArray(saved.cfCols)) {
        const defaultCf = cf.filter(c => c.field_type === 'boolean').map(c => c.id);
        setVisibleCfCols(new Set(defaultCf));
      }
    } catch (err) { setError(err); }
    finally { setLoading(false); }
  };

  // All registration field columns are available in the picker (v50c-3c-2b).
  // Previously this was filtered to "fields with at least one non-empty value"
  // which prevented organisers from preparing their check-in view BEFORE
  // people registered. Now: show all, user picks, empty cells render "—".
  const availableRegCols = useMemo(() => REG_DISPLAY_COLS, []);

  // Custom reg fields: show all that are defined for this event, regardless
  // of whether any participant has supplied a value yet.
  const availableCfCols = useMemo(() => customFieldDefs, [customFieldDefs]);

  const handleAddField = async (e) => {
    e.preventDefault();
    if (!newFieldName.trim()) return;
    try {
      const created = await checkinApi.createField(eventId, { field_name: newFieldName.trim(), sort_order: tickFields.length });
      setNewFieldName('');
      setShowCreateField(false);
      await loadAll();
      setVisibleTickCols(prev => new Set([...prev, created.id]));
    } catch (err) { setError(err); }
  };

  // Column drag-and-drop reorder (separate from PeopleTable order)
  const handleCiColDrop = (dragId, dropId) => {
    if (dragId === dropId) return;
    // Build a flat ordered list of all non-fixed draggable column ids.
    // v0.50e-1d: group_code dropped from fixed list — it's a toggleable
    // reg column now, so it appears in visibleRegList when enabled.
    const allDraggable = [
      'name', 'checkin',
      ...visibleTickList.map(f => 'tick_' + f.id),
      ...visibleRegList.map(c => 'reg_' + c.id),
      ...visibleCfList.map(c => 'cf_' + c.id),
      ...(showNotes ? ['notes'] : []),
    ];
    const ordered = colOrder.length > 0
      ? [...colOrder.filter(id => allDraggable.includes(id)), ...allDraggable.filter(id => !colOrder.includes(id))]
      : allDraggable;
    const from = ordered.indexOf(dragId);
    const to = ordered.indexOf(dropId);
    if (from === -1 || to === -1) return;
    const next = [...ordered];
    next.splice(from, 1);
    next.splice(to, 0, dragId);
    setColOrder(next);
    if (ciOrderKey) { try { localStorage.setItem(ciOrderKey, JSON.stringify(next)); } catch {} }
    setDragColId(null);
  };


  const handleDeleteField = async (fieldId) => {
    const ok = await confirm({
      title: t('checkin.delete_column.title'),
      message: t('checkin.delete_column.message'),
      confirmLabel: t('checkin.delete_column.confirm'),
      danger: true,
    });
    if (!ok) return;
    try { await checkinApi.deleteField(eventId, fieldId); await loadAll(); }
    catch (err) { setError(err); }
  };

  const handleToggle = async (participantId, fieldId) => {
    const key = `${participantId}:${fieldId}`;
    const current = values[key] || false;
    try {
      await checkinApi.toggleValue(eventId, participantId, fieldId, !current);
      setValues(prev => ({ ...prev, [key]: !current }));
    } catch (err) { setError(err); }
  };

  // v50c-3c-2b: optimistic check-in toggle. Previously did a full
  // window.location.reload() after each click — jarring and visibly laggy.
  // Now: flip local state instantly, PATCH in background, clear the
  // optimistic entry when the PATCH completes (parent will eventually
  // refresh participantList via its own mechanism).
  const [optimisticCheckins, setOptimisticCheckins] = useState({}); // {id: bool}
  // v1.0-pre #3: optimistic check-in *timestamp*. Mirrors the boolean above
  // so the "Check-in Time" column updates immediately, not only after the
  // next parent refetch. Map: {id: ISO string | null}.
  const [optimisticCheckinAt, setOptimisticCheckinAt] = useState({});
  const [checkinPending, setCheckinPending] = useState({}); // {id: true}

  const handleCheckin = async (participantId, currentStatus) => {
    const next = !currentStatus;
    // Optimistic flip — both the boolean and the timestamp, so the
    // "Check-in Time" column reflects the change immediately.
    const nowIso = next ? new Date().toISOString() : null;
    setOptimisticCheckins(prev => ({ ...prev, [participantId]: next }));
    setOptimisticCheckinAt(prev => ({ ...prev, [participantId]: nowIso }));
    setCheckinPending(prev => ({ ...prev, [participantId]: true }));
    try {
      await participantsApi.checkin(participantId, next);
      // Success — keep the optimistic entries (so the UI stays correct)
      // until the next parent refresh drops them.
    } catch (err) {
      // Rollback both optimistic flips on failure
      setOptimisticCheckins(prev => {
        const copy = { ...prev };
        delete copy[participantId];
        return copy;
      });
      setOptimisticCheckinAt(prev => {
        const copy = { ...prev };
        delete copy[participantId];
        return copy;
      });
      setError(err);
    } finally {
      setCheckinPending(prev => {
        const copy = { ...prev };
        delete copy[participantId];
        return copy;
      });
    }
  };

  // Helper — returns the effective checked_in value for a participant,
  // preferring the optimistic override if one exists.
  const isCheckedIn = (p) =>
    (p.id in optimisticCheckins) ? optimisticCheckins[p.id] : !!p.checked_in;

  // Helper — same idea for the timestamp. Returns ISO string or null.
  const getCheckedInAt = (p) =>
    (p.id in optimisticCheckinAt) ? optimisticCheckinAt[p.id] : (p.checked_in_at || null);

  // Clear optimistic entries when the upstream participantList genuinely
  // reflects them (prevents stale overrides if the parent ever re-fetches).
  useEffect(() => {
    setOptimisticCheckins(prev => {
      const next = {};
      for (const [idStr, val] of Object.entries(prev)) {
        const id = Number(idStr);
        const p = participantList.find(x => x.id === id);
        // Keep the override only if upstream hasn't caught up yet.
        if (p && !!p.checked_in !== val) next[id] = val;
      }
      return next;
    });
    setOptimisticCheckinAt(prev => {
      const next = {};
      for (const [idStr, val] of Object.entries(prev)) {
        const id = Number(idStr);
        const p = participantList.find(x => x.id === id);
        // Keep the override if upstream hasn't caught up. We compare by
        // truthiness rather than exact-string equality because the server
        // will set its own timestamp on the next refetch and we don't want
        // a hairline mismatch to keep our optimistic value alive forever.
        if (p && !!p.checked_in_at !== !!val) next[id] = val;
      }
      return next;
    });
  }, [participantList]);

  // v1.0-pre #8: subscribe to SSE for cross-device check-in sync. When
  // another staff device ticks someone in, the server publishes to the
  // checkin:<event_id> topic and we merge the change into the local
  // optimistic state so the UI updates without a refresh. The same
  // optimistic-clearing useEffect above will drop these once the parent
  // refetches and confirms the change. Tick-field changes (per-column)
  // arrive as `checkin_value_changed` and update `values` directly.
  useEventStream({
    eventId,
    surface: 'checkin',
    onEvent: (msg) => {
      if (!msg) return;
      if (msg.type === 'checkin_changed') {
        const pid = msg.participant_id;
        if (!pid) return;
        setOptimisticCheckins(prev => ({ ...prev, [pid]: !!msg.checked_in }));
        setOptimisticCheckinAt(prev => ({ ...prev, [pid]: msg.checked_in_at || null }));
      } else if (msg.type === 'checkin_value_changed') {
        const key = `${msg.participant_id}:${msg.field_id}`;
        setValues(prev => ({ ...prev, [key]: !!msg.checked }));
      }
    },
  });

  const openColPicker = () => {
    if (colPickerBtnRef.current) {
      const rect = colPickerBtnRef.current.getBoundingClientRect();
      setColPickerPos({ top: rect.bottom + 6, right: window.innerWidth - rect.right });
    }
    setShowColPicker(v => !v);
  };

  useEffect(() => {
    if (!showColPicker) return;
    const handler = (e) => {
      if (!e.target.closest('[data-col-picker]') && !colPickerBtnRef.current?.contains(e.target)) {
        setShowColPicker(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showColPicker]);

  const toggleRegCol = (id) => setVisibleRegCols(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); saveCiCols({ regCols: [...n] }); return n; });
  const toggleTickCol = (id) => setVisibleTickCols(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); saveCiCols({ tickCols: [...n] }); return n; });
  const toggleCfCol = (id) => setVisibleCfCols(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); saveCiCols({ cfCols: [...n] }); return n; });

  // v0.70d-2a-1: Check-in shows only active (non-cancelled) participants.
  // Cancelled participants remain visible in PeopleTable for audit history
  // — event day is for people actually attending, so they don't belong
  // here. Mirrors AllocationBoard's `activeParticipants` pattern.
  // `participantList` (raw prop) is still used for dependency arrays and
  // id lookups (e.g. the optimistic-checkin cleanup at line 289 needs
  // to find a participant by id even if they were just cancelled).
  const activeParticipantList = useMemo(
    () => participantList.filter(p => p.registration_status !== 'cancelled'),
    [participantList]
  );

  const filtered = useMemo(() => {
    let list = [...activeParticipantList];
    if (checkinFilter === 'checked_in') list = list.filter(p => p.checked_in);
    else if (checkinFilter === 'not_checked_in') list = list.filter(p => !p.checked_in);
    if (search.trim()) {
      const q = search.toLowerCase();
      const matchingMarkIds = new Set(
        markDefs.filter(m => m.name.toLowerCase().includes(q)).map(m => String(m.id))
      );
      list = list.filter(p => {
        if (`${p.first_name} ${p.last_name}`.toLowerCase().includes(q)) return true;
        if (p.email?.toLowerCase().includes(q)) return true;
        if (p.group_code?.toLowerCase().includes(q)) return true;
        if (String(p.participant_number || '').includes(q)) return true;
        if (matchingMarkIds.size > 0) {
          const pMarkIds = new Set((markAssignments[String(p.id)] || []).map(a => String(a.mark_id)));
          if ([...matchingMarkIds].some(id => pMarkIds.has(id))) return true;
        }
        return false;
      });
    }
    list.sort((a, b) => {
      let va, vb;
      switch (sortCol) {
        case 'participant_number': va = a.participant_number || 0; vb = b.participant_number || 0; break;
        case 'name': va = `${a.first_name} ${a.last_name}`; vb = `${b.first_name} ${b.last_name}`; break;
        case 'group_code': va = a.group_code || ''; vb = b.group_code || ''; break;
        case 'checkin': va = a.checked_in ? '1' : '0'; vb = b.checked_in ? '1' : '0'; break;
        default: va = a.participant_number || 0; vb = b.participant_number || 0;
      }
      if (typeof va === 'string') { va = va.toLowerCase(); vb = vb.toLowerCase(); }
      if (va < vb) return sortDir === 'asc' ? -1 : 1;
      if (va > vb) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return list;
  }, [activeParticipantList, search, checkinFilter, sortCol, sortDir, markDefs, markAssignments]);

  if (loading) return <p className="text-gray-400 dark:text-gray-400 text-sm">{t('common.loading')}</p>;

  // v0.70d-2e-4-1: use the optimistic-aware helper so checkedInCount
  // reflects fresh check-ins immediately, not after the next parent
  // reload. Pre-fix, the row checkbox + tint flipped optimistically
  // but checkedInCount filtered the raw prop — leading to a visibly
  // out-of-sync top-progress + count line ("1 of 4 checked in" with
  // three yellow rows visible). The lag was invisible pre-2e-4 because
  // checkedInCount lived only in the small inline count line; C2's
  // new top-progress made it a hero metric and the staleness landed.
  const checkedInCount = activeParticipantList.filter(isCheckedIn).length;

  const visibleTickList = tickFields.filter(f => visibleTickCols.has(f.id));
  const visibleRegList = availableRegCols.filter(c => visibleRegCols.has(c.id));
  const visibleCfList = availableCfCols.filter(cf => visibleCfCols.has(cf.id));
  const hasColOptions = availableRegCols.length > 0 || tickFields.length > 0 || availableCfCols.length > 0;

  const renderRegCell = (p, col) => {
    if (col.id === 'reg_dob') return <span className="text-muted text-xs">{p.date_of_birth ? formatDate(p.date_of_birth) : '—'}</span>;
    if (col.id === 'reg_gender') return <span className="text-muted text-xs">{p.gender ? (p.gender === 'male' ? t('people.gender.male') : t('people.gender.female')) : '—'}</span>;
    if (col.id === 'reg_checkin_at') {
      // v1.0-pre #3: read through getCheckedInAt so optimistic flips show
      // immediately, not only after the parent refetches participantList.
      const ts = getCheckedInAt(p);
      return <span className="text-muted text-xs">{ts ? new Date(ts).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' }) : '—'}</span>;
    }
    if (!col.render) return <span className="text-muted text-xs">—</span>;
    return <span className="text-muted text-xs">{col.render(p)}</span>;
  };

  return (
    <div>
      <TranslatedError err={error} className="text-sm rounded-lg p-3 mb-4" />

      {/* ── Toolbar ── */}
      <div className="px-4 py-3 border-b border-gray-100 dark:border-white/10 space-y-2">
        {/* Row 1: Search */}
        <div className="relative">
          <input type="text" {...{placeholder: t('checkin.search')}} value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full border border-gray-200 dark:border-white/15 rounded-lg pl-8 pr-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-steel-blue" />
          <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-subtle text-sm">🔍</span>
        </div>

        {/* v0.70d-2e-4 (C2): top-of-panel overall progress indicator.
            Replaces the per-category allocation-status banner (removed
            below) which answered an analytical question more
            appropriate for retrospective review. Live-ops needs the
            singular question: "how many in?" — that's this single
            line. Always visible. Tracks live pace.
            checkedInCount is computed at line ~376; this just
            renders it inline above the existing count line. The
            progress bar reuses AB9's crossfade pattern (neutral grey
            <50%, io-accent fade-in ≥50%) for consistency with the
            other progress bars across the app. Per-category
            breakdown still has a home on EventDetailPage's stats
            section for retrospective review. */}
        {activeParticipantList.length > 0 && (() => {
          const pct = Math.round((checkedInCount / activeParticipantList.length) * 100);
          return (
            <div className="flex items-center gap-3">
              <div className="flex-1 rounded-full h-1.5" style={{ background: 'var(--neutral-tint)' }}>
                <div className="rounded-full h-1.5 transition-all"
                  style={{
                    width: `${pct}%`,
                    backgroundImage: 'linear-gradient(to right, rgba(120,120,120,0.55) 0%, rgba(120,120,120,0.55) 50%, var(--io-accent) 100%)',
                    backgroundSize: pct > 0 ? `${10000 / pct}% 100%` : '100% 100%',
                    backgroundRepeat: 'no-repeat',
                  }} />
              </div>
              <span className="text-xs font-semibold shrink-0 font-mono"
                style={{ color: 'var(--io-accent)' }}>
                {t('checkin.top_progress', { checked: checkedInCount, total: activeParticipantList.length })}
              </span>
            </div>
          );
        })()}

        {/* Row 2: Count */}
        <div className="text-[10px] text-gray-400 dark:text-gray-400">
          {filtered.length < activeParticipantList.length
            ? t('checkin.count_filtered').replace('{count}', filtered.length).replace('{total}', activeParticipantList.length)
            : t('checkin.count_total').replace('{count}', activeParticipantList.length).replace('{total}', activeParticipantList.length)
          }
          {' · '}
          {t('checkin.count_checkedin').replace('{n}', checkedInCount).replace('{total}', activeParticipantList.length)}
        </div>

        {/* Row 3: Filter pills + controls, all left */}
        <div className="flex items-center gap-2 flex-wrap">
          {[['', t('common.all')], ['checked_in', t('checkin.filter.checked_in')], ['not_checked_in', t('checkin.filter.not_checked_in')]].map(([val, label]) => (
            <button key={val} onClick={() => setCheckinFilter(checkinFilter === val ? '' : val)}
              className={`text-[10px] px-2.5 py-1 rounded-full font-medium transition-colors ${
                checkinFilter === val ? 'bg-steel-blue text-white' : 'bg-gray-100 dark:bg-white/10 text-muted hover:bg-gray-200 dark:bg-white/15'
              }`}>
              {label}
            </button>
          ))}
          {(isAdmin || canViewColumns) && hasColOptions && (
            <button ref={colPickerBtnRef} onClick={openColPicker}
              className="text-xs text-muted hover:text-mid-navy border border-gray-200 dark:border-white/15 rounded-lg px-3 py-1.5 hover:border-gray-300 dark:border-white/25">
              {t('checkin.columns')}
            </button>
          )}
          {canCreateColumns && (
            <button onClick={() => { setShowCreateField(v => !v); setShowColPicker(false); }}
              className="text-xs text-muted hover:text-mid-navy border border-gray-200 dark:border-white/15 rounded-lg px-3 py-1.5 hover:border-gray-300 dark:border-white/25 transition-colors">
              {showCreateField ? t('common.cancel') : t('checkin.create_column')}
            </button>
          )}
        </div>
      </div>

      {/* v0.70d-2e-4 (C2): allocation-status banner removed.
          The per-category breakdown answered an analytical
          question (how each category's coverage progresses)
          that was useful for retrospective review but wrong for
          live ops — there the question is singular: "how many
          in?" That singular answer now lives at the top of the
          panel below the search bar (top-of-panel overall
          progress indicator added in the toolbar block above).
          Per-category breakdown still has a home on
          EventDetailPage's stats section. */}

      {showColPicker && (
        <div data-col-picker
          className="fixed border rounded-lg shadow-xl z-50 min-w-[220px] max-h-80 overflow-y-auto py-2 px-3"
          style={{
            top: colPickerPos.top,
            right: colPickerPos.right,
            background: 'var(--card-bg-solid)',
            borderColor: 'var(--card-border)',
            color: 'var(--text-primary)',
          }}>
          <p className="text-[9px] text-gray-400 dark:text-gray-400 uppercase tracking-wide font-semibold mb-2">{t('checkin.show_hide')}</p>

          {tickFields.length > 0 && (
            <>
              <p className="text-[9px] text-subtle uppercase tracking-wide mb-1">{t('checkin.columns.tracking')}</p>
              {tickFields.map(f => (
                <label key={f.id} className="flex items-center gap-2 py-0.5 text-xs cursor-pointer hover:text-deep-navy dark:hover:text-off-white">
                  <input type="checkbox" checked={visibleTickCols.has(f.id)} onChange={() => toggleTickCol(f.id)} className="h-3 w-3 rounded" />
                  {f.field_name}
                </label>
              ))}
            </>
          )}

          {availableRegCols.length > 0 && (
            <>
              <p className="text-[9px] text-subtle uppercase tracking-wide mb-1 mt-3">{t('checkin.columns.registration')}</p>
              {availableRegCols.map(col => (
                <label key={col.id} className="flex items-center gap-2 py-0.5 text-xs cursor-pointer hover:text-deep-navy dark:hover:text-off-white">
                  <input type="checkbox" checked={visibleRegCols.has(col.id)} onChange={() => toggleRegCol(col.id)} className="h-3 w-3 rounded" />
                  {colLabel(col.label)}
                </label>
              ))}
            </>
          )}

          {availableCfCols.length > 0 && (
            <>
              <p className="text-[9px] text-subtle uppercase tracking-wide mb-1 mt-3">{t('checkin.columns.custom')}</p>
              {availableCfCols.map(cf => (
                <label key={cf.id} className="flex items-center gap-2 py-0.5 text-xs cursor-pointer hover:text-deep-navy dark:hover:text-off-white">
                  <input type="checkbox" checked={visibleCfCols.has(cf.id)} onChange={() => toggleCfCol(cf.id)} className="h-3 w-3 rounded" />
                  {cf.label}
                </label>
              ))}
            </>
          )}

          <p className="text-[9px] text-subtle uppercase tracking-wide mb-1 mt-3">{t('checkin.columns.other')}</p>
          <label className="flex items-center gap-2 py-0.5 text-xs cursor-pointer hover:text-deep-navy dark:hover:text-off-white">
            <input type="checkbox" checked={showNotes} onChange={() => { setShowNotes(v => { saveCiCols({ showNotes: !v }); return !v; }); }} className="h-3 w-3 rounded" />
            {t('common.notes')}
          </label>
          <button onClick={() => setShowColPicker(false)} className="mt-3 text-[10px] text-gray-400 dark:text-gray-400 hover:text-gray-600">{t('common.close')}</button>
        </div>
      )}

      {/* Create column form */}
      {showCreateField && (
        <div className="bg-gray-50 dark:bg-white/5 rounded-xl p-4 mb-4">
          <p className="text-[10px] text-gray-400 dark:text-gray-400 mb-2">{t('checkin.create_column.hint')}</p>
          <form onSubmit={handleAddField} className="flex gap-2">
            <input type="text" {...{placeholder: t('checkin.column_name')}} value={newFieldName}
              onChange={e => setNewFieldName(e.target.value)} required autoFocus
              className="flex-1 border border-gray-200 dark:border-white/15 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-steel-blue" />
            <button type="submit" className="bg-steel-blue text-white text-xs font-semibold px-4 py-1.5 rounded-lg hover:bg-mid-navy shrink-0">{t('common.add')}</button>
          </form>
        </div>
      )}

      {/* Desktop table — hidden on mobile */}
      <div className="hidden md:block overflow-x-auto">
          <table className="w-full min-w-max text-sm">
            <thead>
              <tr className="bg-gray-50 dark:bg-white/5 text-left text-xs text-muted uppercase tracking-wide">
                <th onClick={() => handleSort('participant_number')} className="px-4 py-2 sticky left-0 bg-gray-50 dark:bg-white/5 z-10 cursor-pointer hover:text-mid-navy select-none whitespace-nowrap">{t('checkin.participant_number')}{sortArrow('participant_number')}</th>
                {/* Draggable columns — Name is draggable too.
                    v0.50e-1d: group_code moved to visibleRegList (toggleable). */}
                {[
                  { id: 'name', label: t('common.name') },
                  { id: 'checkin', label: t('checkin.title'), center: true },
                  ...visibleTickList.map(f => ({ id: 'tick_' + f.id, label: f.field_name, center: true, tickId: f.id })),
                  ...visibleRegList.map(c => ({ id: 'reg_' + c.id, label: colLabel(c.label) })),
                  ...visibleCfList.map(cf => ({ id: 'cf_' + cf.id, label: cf.label })),
                  ...(showNotes ? [{ id: 'notes', label: t('common.notes'), center: true }] : []),
                ].sort((a, b) => {
                  if (!colOrder.length) return 0;
                  const ai = colOrder.indexOf(a.id), bi = colOrder.indexOf(b.id);
                  if (ai === -1 && bi === -1) return 0;
                  if (ai === -1) return 1; if (bi === -1) return -1;
                  return ai - bi;
                }).map(col => (
                  <th key={col.id}
                    draggable
                    onDragStart={() => setDragColId(col.id)}
                    onDragOver={e => { if (dragColId && dragColId !== col.id) e.preventDefault(); }}
                    onDrop={() => { if (dragColId) handleCiColDrop(dragColId, col.id); }}
                    onDragEnd={() => setDragColId(null)}
                    onClick={() => handleSort(col.id)}
                    className={`px-4 py-2 cursor-move select-none transition-opacity ${col.center ? 'text-center' : ''} ${dragColId === col.id ? 'opacity-40' : ''}`}>
                    <span className="text-subtle mr-1 text-[10px]">⠿</span>
                    {col.label}{sortArrow(col.id)}
                    {col.tickId && canCreateColumns && (
                      <button onClick={() => handleDeleteField(col.tickId)} className="text-red-300 hover:text-red-500 text-[10px] ml-1">✕</button>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(p => {
                const ci = isCheckedIn(p);
                const pending = !!checkinPending[p.id];
                return (
                <tr key={p.id} className={`border-t border-gray-50 dark:border-white/5 transition-colors ${ci ? 'bg-steel-blue/[0.12] dark:bg-gold/[0.18]' : ''}`} style={ci ? { boxShadow: 'inset 4px 0 0 0 var(--accent-checked)' } : undefined}>
                  <td className={`px-4 py-2 font-mono text-xs text-gray-400 dark:text-gray-400 sticky left-0 z-10 ${ci ? 'bg-steel-blue/5 dark:bg-gold/10' : 'bg-white dark:bg-white/5'}`}>
                    #{p.participant_number || '—'}
                  </td>
                  {[
                    { id: 'name' },
                    { id: 'checkin' },
                    ...visibleTickList.map(f => ({ id: 'tick_' + f.id, tickField: f })),
                    ...visibleRegList.map(c => ({ id: 'reg_' + c.id, regCol: c })),
                    ...visibleCfList.map(cf => ({ id: 'cf_' + cf.id, cfField: cf })),
                    ...(showNotes ? [{ id: 'notes' }] : []),
                  ].sort((a, b) => {
                    if (!colOrder.length) return 0;
                    const ai = colOrder.indexOf(a.id), bi = colOrder.indexOf(b.id);
                    if (ai === -1 && bi === -1) return 0;
                    if (ai === -1) return 1; if (bi === -1) return -1;
                    return ai - bi;
                  }).map(col => {
                    if (col.id === 'name') return (
                      <td key="name" className={`px-4 py-2 font-medium whitespace-nowrap text-body`}>
                        <span className="flex items-center gap-1">
                          {p.first_name} {p.last_name}
                          <MarkDots marksForParticipant={getParticipantMarks(p.id, 'checkin')}
                            onManage={() => setMarkModal(p)} />
                          {/* v1.0-pre: insight ⓘ — desktop entry point to the
                              InsightPanel slide-out. Mirrors the mobile ⓘ at
                              line ~739; same handler, same panel. Styled to
                              match the rest of the table at 40% opacity idle,
                              100% on hover. */}
                          <button
                            onClick={() => setInsightParticipant(p)}
                            aria-label={t('insight.open')}
                            title={t('insight.open')}
                            className="shrink-0 text-[12px] leading-none px-1 opacity-40 hover:opacity-100 transition-opacity"
                            style={{ color: 'var(--text-subtle)' }}>
                            ⓘ
                          </button>
                        </span>
                      </td>
                    );
                    if (col.id === 'checkin') return (
                      <td key="checkin" className="px-4 py-2 text-center">
                        <button
                          onClick={() => handleCheckin(p.id, ci)}
                          disabled={pending}
                          className={`w-7 h-7 rounded border-2 inline-flex items-center justify-center transition-colors text-sm font-bold ${
                            ci
                              ? 'bg-steel-blue border-steel-blue text-white dark:bg-gold dark:border-gold dark:text-deep-navy'
                              : 'border-gray-300 dark:border-white/50 text-transparent hover:border-steel-blue dark:hover:border-gold'
                          } ${pending ? 'opacity-60 cursor-wait' : ''}`}
                        >✓</button>
                      </td>
                    );
                    if (col.tickField) {
                      const f = col.tickField;
                      const key = `${p.id}:${f.id}`;
                      const checked = values[key] || false;
                      return (
                        <td key={col.id} className="px-4 py-2 text-center">
                          <button onClick={() => handleToggle(p.id, f.id)}
                            className={`w-7 h-7 rounded border-2 inline-flex items-center justify-center transition-colors text-sm font-bold ${
                              checked ? 'bg-steel-blue border-steel-blue text-white' : 'border-gray-300 dark:border-white/25 text-transparent hover:border-steel-blue'
                            }`}>✓</button>
                        </td>
                      );
                    }
                    if (col.regCol) return <td key={col.id} className="px-4 py-2">{renderRegCell(p, col.regCol)}</td>;
                    if (col.cfField) return (
                      <td key={col.id} className="px-4 py-2">
                        <span className="text-muted text-xs">{p.custom_fields?.[col.cfField.id] || '—'}</span>
                      </td>
                    );
                    if (col.id === 'notes') return (
                      <td key="notes" className="px-4 py-2 text-center">
                        {(() => { const nc = noteCounts?.[`participant:${p.id}`] || 0; return (
                          <button onClick={() => onOpenNotes && onOpenNotes(p)} className="text-xs text-steel-blue hover:text-mid-navy">
                            {t('common.notes')}{nc > 0 && <span className="ml-0.5 bg-steel-blue text-white text-[8px] px-1 py-0 rounded-full">{nc}</span>}
                          </button>
                        ); })()}
                      </td>
                    );
                    return null;
                  })}
                </tr>
              );
              })}
            </tbody>
          </table>
        </div>

      {/* v0.58f: Mobile card view — shown below md breakpoint.
          Parallel to the desktop table. Preserves every interaction
          (check-in tap, tick-field toggles, marks, notes) without
          requiring horizontal scroll.

          Extra-column pills: each visible tick field, reg column, and
          custom field gets a pill on the card. Tick-field pills are
          tappable (same handleToggle as desktop). Reg and custom-field
          pills are read-only readable info. */}
      <div className="md:hidden space-y-2 px-4 mt-2">
        {filtered.map(p => {
          const ci = isCheckedIn(p);
          const pending = !!checkinPending[p.id];
          const pMarks = getParticipantMarks(p.id, 'checkin');
          const nc = noteCounts?.[`participant:${p.id}`] || 0;
          // v0.58g: count non-empty reg + cf pills for this participant.
          // These are the ones we hide-by-default behind a "▸ N details"
          // toggle. Tick-field pills are ALWAYS visible on mobile — they
          // are the actual hot-path check-in work at the door.
          // v0.70d-2d-2 (C7): explicit per-column presence check —
          // previously, columns with `field === null` always counted as
          // having data (because the filter returned true for them
          // unconditionally), so the "▸ N details" toggle showed even
          // when reg_registered_at and reg_checkin_at had no values for
          // a participant. Mirrors PeopleTable's `hasHiddenDetails`
          // pattern (switch on column id for the null-field cases).
          const regPillsWithData = visibleRegList.filter(c => {
            if (c.field) {
              const val = p[c.field];
              return val !== null && val !== undefined && val !== '';
            }
            // field === null: presence depends on the underlying source
            if (c.id === 'reg_registered_at') return !!p.created_at;
            if (c.id === 'reg_checkin_at')    return !!getCheckedInAt(p);
            return false;
          });
          const cfPillsWithData = visibleCfList.filter(cf => !!p.custom_fields?.[cf.id]);
          const hiddenPillCount = regPillsWithData.length + cfPillsWithData.length;
          const expanded = mobileExpandedIds.has(p.id);
          return (
            <div key={p.id}
              className={`card-surface-solid rounded-2xl p-3 ${ci ? 'bg-steel-blue/[0.12] dark:bg-gold/[0.18]' : ''}`}
              style={{
                border: '1px solid var(--card-border)',
                borderLeft: ci ? '4px solid var(--accent-checked)' : '1px solid var(--card-border)',
              }}>
              {/* Row 1: big check-in button, participant number, name, marks */}
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handleCheckin(p.id, ci)}
                  disabled={pending}
                  aria-label={ci ? t('checkin.uncheck') : t('checkin.check')}
                  className={`shrink-0 w-10 h-10 rounded-lg border-2 inline-flex items-center justify-center transition-colors text-lg font-bold ${
                    ci
                      ? 'bg-steel-blue border-steel-blue text-white dark:bg-gold dark:border-gold dark:text-deep-navy'
                      : 'border-gray-300 dark:border-white/50 text-transparent hover:border-steel-blue dark:hover:border-gold'
                  } ${pending ? 'opacity-60 cursor-wait' : ''}`}>
                  ✓
                </button>
                <span className="font-mono text-[11px] shrink-0"
                  style={{ color: 'var(--text-subtle)' }}>
                  #{String(p.participant_number || '—').padStart(3, '0')}
                </span>
                {/* v0.83 #26: name + marks grouped, ⓘ separate. The
                    inner flex takes flex-1 so it fills the row; name
                    truncates if needed; MarkDots sit immediately after.
                    ⓘ is shrink-0 at the row's right edge.  */}
                <div className="flex items-center gap-1 min-w-0 flex-1">
                  <span className="font-medium text-sm truncate min-w-0"
                    style={{ color: 'var(--text-primary)' }}>
                    {p.first_name} {p.last_name}
                  </span>
                  <MarkDots marksForParticipant={pMarks}
                    onManage={() => setMarkModal(p)} />
                </div>
                {/* v0.61a: insight ⓘ — mobile-only entry point to the
                    same panel the Organise board uses. Styled to match
                    AllocationBoard.jsx for visual consistency (40% opacity
                    idle, 100% on touch/hover). */}
                <button
                  onClick={() => setInsightParticipant(p)}
                  aria-label={t('insight.open')}
                  title={t('insight.open')}
                  className="shrink-0 text-[12px] leading-none px-1 opacity-40 hover:opacity-100 transition-opacity"
                  style={{ color: 'var(--text-subtle)' }}>
                  ⓘ
                </button>
              </div>

              {/* Row 2: tick-field pills (tappable) */}
              {visibleTickList.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {visibleTickList.map(f => {
                    const key = `${p.id}:${f.id}`;
                    const checked = values[key] || false;
                    return (
                      <button key={f.id}
                        onClick={() => handleToggle(p.id, f.id)}
                        className="inline-flex items-center gap-1 text-[11px] px-2 py-1 rounded-full transition-colors"
                        style={{
                          background: checked ? 'var(--io-accent)' : 'var(--app-bg)',
                          color: checked ? 'white' : 'var(--text-muted)',
                          border: `1px solid ${checked ? 'var(--io-accent)' : 'var(--card-border)'}`,
                        }}>
                        <span className="text-[10px]">{checked ? '✓' : '○'}</span>
                        <span>{f.field_name}</span>
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Footer row: details toggle + notes button share a row
                  so they have visual separation instead of bumping into
                  each other (v0.58f-1 rendered "4 detailsNotes" on one
                  line with no gap). */}
              {(hiddenPillCount > 0 || showNotes) && !expanded && (
                <div className="flex items-center justify-between mt-3 gap-3">
                  {hiddenPillCount > 0 ? (
                    <button
                      onClick={() => toggleMobileExpanded(p.id)}
                      className="text-[11px] hover:underline"
                      style={{ color: 'var(--text-subtle)' }}>
                      ▸ {t('checkin.show_details', { n: hiddenPillCount })}
                    </button>
                  ) : <span />}
                  {showNotes && (
                    <button
                      onClick={() => onOpenNotes && onOpenNotes(p)}
                      className="text-xs font-semibold hover:underline"
                      style={{ color: 'var(--io-accent)' }}>
                      {t('common.notes')}{nc > 0 && (
                        <span className="ml-1 bg-steel-blue text-white text-[9px] px-1.5 py-0 rounded-full">
                          {nc}
                        </span>
                      )}
                    </button>
                  )}
                </div>
              )}

              {/* Reg-column pills (read-only info) — hidden by default */}
              {visibleRegList.length > 0 && expanded && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {visibleRegList.map(c => {
                    const val = c.field ? p[c.field] : null;
                    const hasData =
                      c.field === null || (val !== null && val !== undefined && val !== '');
                    if (!hasData) return null;
                    return (
                      <span key={c.id}
                        className="inline-flex items-center gap-1 text-[11px] px-2 py-1 rounded-full"
                        style={{
                          background: 'var(--app-bg)',
                          color: 'var(--text-muted)',
                          border: '1px solid var(--card-border)',
                        }}>
                        <span className="font-semibold"
                          style={{ color: 'var(--text-subtle)' }}>
                          {colLabel(c.label)}:
                        </span>
                        <span>{renderRegCell(p, c)}</span>
                      </span>
                    );
                  })}
                </div>
              )}

              {/* Custom-field pills (read-only) — hidden by default */}
              {visibleCfList.length > 0 && expanded && (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {visibleCfList.map(cf => {
                    const val = p.custom_fields?.[cf.id];
                    if (!val) return null;
                    return (
                      <span key={cf.id}
                        className="inline-flex items-center gap-1 text-[11px] px-2 py-1 rounded-full"
                        style={{
                          background: 'var(--app-bg)',
                          color: 'var(--text-muted)',
                          border: '1px solid var(--card-border)',
                        }}>
                        <span className="font-semibold"
                          style={{ color: 'var(--text-subtle)' }}>
                          {cf.label}:
                        </span>
                        <span>{val}</span>
                      </span>
                    );
                  })}
                </div>
              )}

              {/* Footer when expanded: hide-details + notes on the same row */}
              {expanded && (
                <div className="flex items-center justify-between mt-3 gap-3">
                  <button
                    onClick={() => toggleMobileExpanded(p.id)}
                    className="text-[11px] hover:underline"
                    style={{ color: 'var(--text-subtle)' }}>
                    ▴ {t('checkin.hide_details')}
                  </button>
                  {showNotes && (
                    <button
                      onClick={() => onOpenNotes && onOpenNotes(p)}
                      className="text-xs font-semibold hover:underline"
                      style={{ color: 'var(--io-accent)' }}>
                      {t('common.notes')}{nc > 0 && (
                        <span className="ml-1 bg-steel-blue text-white text-[9px] px-1.5 py-0 rounded-full">
                          {nc}
                        </span>
                      )}
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
      {filtered.length === 0 && (
        <div className="p-5">
          <EmptyState
            compact
            title={search
              ? (t('checkin.empty_search.title'))
              : (t('checkin.empty.title'))}
            hint={search
              ? (t('checkin.empty_search.hint'))
              : (t('checkin.empty.hint'))}
          />
        </div>
      )}
      <ConfirmOverlay />
      {markModal && (
        <MarkAssignModal
          participant={markModal}
          defs={markDefs}
          assignments={markAssignments}
          onAssign={async (markId, participantId) => { await assignMark(markId, participantId); }}
          onUnassign={async (markId, participantId) => { await unassignMark(markId, participantId); }}
          view="checkin"
          canAssign={canAssignMarks}
          onClose={() => setMarkModal(null)} />
      )}
      {/* v0.61a: Insight panel — self-gates on participant={null} so an
          unconditional mount is safe. Passes the checkin-view marks so the
          mark-dots rendered inside the panel match what's visible on the
          card the user tapped ⓘ on. */}
      <InsightPanel
        participant={insightParticipant}
        eventId={eventId}
        marksForPerson={insightParticipant ? getParticipantMarks(insightParticipant.id, 'checkin') : []}
        isAdmin={isAdmin}
        onClose={() => setInsightParticipant(null)}
      />
    </div>
  );
}
