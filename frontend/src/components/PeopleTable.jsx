import { useState, useMemo, useEffect, useRef } from 'react';
import { participants as participantsApi, customFields as cfApi, getToken } from '../services/api';
import { useDateFormat } from '../hooks/useDateFormat';
import { useI18n } from '../hooks/useI18n';
import { useToast } from '../hooks/useToast';
import { useConfirmOverlay } from './ConfirmOverlay';
import { downloadParticipantDataExport } from '../utils/downloadParticipantDataExport';
import MarkDots from './MarkDots';
import MarkAssignModal from './MarkAssignModal';
import MessageViewerModal from './MessageViewerModal';
import EmptyState from './EmptyState';
import { useMarks } from '../hooks/useMarks';
import BatchRegisterModal from './BatchRegisterModal';
import ConfirmEditModal from './ConfirmEditModal';
import GroupCodeTooltip from './GroupCodeTooltip';

// Built-in columns with optional field name for data-detection
const BUILTIN_COLUMNS = [
  { id: 'name', label: 'people.col.name', always: true },
  { id: 'participant_number', label: 'people.col.participant_number', always: true },
  { id: 'email', label: 'people.col.email', default: true },
  { id: 'group_code', label: 'people.col.group_code', default: true },
  { id: 'status', label: 'people.col.status', default: true },
  { id: 'gender', label: 'people.col.gender', field: 'gender' },
  { id: 'date_of_birth', label: 'people.col.date_of_birth', field: 'date_of_birth' },
  { id: 'phone', label: 'people.col.phone', field: 'phone' },
  { id: 'address', label: 'people.col.address', field: 'address' },
  { id: 'country', label: 'people.col.country', field: 'country' },
  { id: 'church_organisation', label: 'people.col.church_organisation', field: 'church_organisation' },
  { id: 'message', label: 'people.col.message', field: 'message' },
  { id: 'registered_at', label: 'people.col.registered_at', default: true },
  { id: 'checked_in', label: 'people.col.checked_in' },
  { id: 'notes', label: 'people.col.notes', default: true },
];

const DEFAULT_COLS = BUILTIN_COLUMNS.filter(c => c.default || c.always).map(c => c.id);
const STATUS_LABELS_KEYS = { pending: 'status.pending', confirmed: 'status.confirmed', cancelled: 'status.cancelled' };

// v1.0-pre #2: editable-field configuration for the People table.
// Drives the inline edit + confirmation-modal flow for fields beyond
// the original name/email/group_code/status set. Each entry maps a
// field id to:
//   - inputType : 'text' | 'tel' | 'select' | 'date' | 'textarea'
//   - labelKey  : i18n key for the field label (used in the confirm modal)
//   - readField : participant attribute to read the current value from
//   - options   : (select only) [{value, labelKey}] for the dropdown
// Status / group_code / name / email are NOT in this map — they keep
// their existing (older) inline-edit code paths to avoid a regressive
// rewrite. New fields ride this generalised flow.
//
// v1.0-pre #13: `message` is intentionally excluded — that field is
// the participant's message TO the organisers; it shouldn't be
// silently overwritten by the organiser. Click on a message cell
// continues to open the read-only MessageViewerModal.
const EDITABLE_FIELDS = {
  gender: {
    inputType: 'select',
    labelKey: 'people.col.gender',
    readField: 'gender',
    options: [
      { value: '',       labelKey: 'common.none' },
      { value: 'male',   labelKey: 'people.gender.male' },
      { value: 'female', labelKey: 'people.gender.female' },
    ],
  },
  date_of_birth: { inputType: 'date',     labelKey: 'people.col.date_of_birth',       readField: 'date_of_birth' },
  phone:         { inputType: 'tel',      labelKey: 'people.col.phone',               readField: 'phone' },
  address:       { inputType: 'text',     labelKey: 'people.col.address',             readField: 'address' },
  country:       { inputType: 'text',     labelKey: 'people.col.country',             readField: 'country' },
  church_organisation: {
                   inputType: 'text',     labelKey: 'people.col.church_organisation', readField: 'church_organisation' },
};
const ALL_STATUSES = ['pending', 'confirmed', 'cancelled'];

export default function PeopleTable({ eventId, userId, participantList, noteCounts, isAdmin, canDelete, marksPerm, onDataChange, onOpenNotes, onDelete, initialStatusFilter = '' }) {
  // v0.50f-1: mark modal opens for everyone (read is implicit). The modal
  // itself renders in view-only mode when canAssign is false. isAdmin
  // bypasses.
  // v0.70d-3c-10: `isAdmin` is historically misnamed — it actually
  // means `canWrite('people')` (admins + staff with people:write).
  // Renaming would touch ~30 sites, so the more surgical fix is the
  // dedicated `canDelete` prop, gated on real admin status only.
  // Used at the three delete-UI sites below; `isAdmin` continues to
  // gate inline edit, status edit, group-code edit, batch register,
  // and the rest of the people-write surface.
  const canAssignMarks = isAdmin || marksPerm === 'write';
  const [search, setSearch] = useState('');
  // v1.0-pre #20: seed the status filter from the optional initial
  // value (passed by EventDetailPage from ?status=). Anything other
  // than the three valid pill ids falls through to '' (All).
  const _seed = ['pending', 'confirmed', 'cancelled'].includes(initialStatusFilter)
    ? initialStatusFilter : '';
  const [statusFilter, setStatusFilter] = useState(_seed);
  const [sortCol, setSortCol] = useState('participant_number');
  const [sortDir, setSortDir] = useState('asc');
  // v0.58g: Which mobile cards have expanded details. Per-session only,
  // Set of participant IDs. Mirrors the pattern from CheckInPanel.
  // v0.61c: persisted to localStorage per (userId, eventId) so the
  // expanded state survives reload — organisers who unfold a few
  // people while reviewing don't lose their place on refresh. Same
  // (userId, eventId)-scoped storage key shape as colsStorageKey
  // below; participantList changes (deletes) are cleaned up lazily
  // on next toggle (the saved IDs are just a Set; missing entries
  // are inert).
  const expandedStorageKey = eventId && userId ? `moimio_people_expanded_${userId}_${eventId}` : null;
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
  const colsStorageKey = eventId && userId ? `moimio_people_cols_${userId}_${eventId}` : null;
  const colOrderKey = eventId && userId ? `moimio_people_col_order_${userId}_${eventId}` : null;
  const [visibleCols, setVisibleCols] = useState(() => {
    if (colsStorageKey) {
      try {
        const saved = localStorage.getItem(colsStorageKey);
        if (saved) return new Set(JSON.parse(saved));
      } catch {}
    }
    return new Set(DEFAULT_COLS);
  });
  // User-defined column order — participant_number always first, then user order
  const [colOrder, setColOrder] = useState(() => {
    if (colOrderKey) {
      try {
        const saved = localStorage.getItem(colOrderKey);
        if (saved) return JSON.parse(saved);
      } catch {}
    }
    return [];
  });
  const [dragColId, setDragColId] = useState(null);
  const [showColPicker, setShowColPicker] = useState(false);
  const [showBatch, setShowBatch] = useState(false);
  // v0.70d-3c-10a + 3c-12: position for the desktop popover variant.
  // 3c-12 added the mobile-modal mode — when colPickerMobile is true,
  // the picker renders as a centred modal with backdrop instead of a
  // positioned popover. The breakpoint is Tailwind's SM (640px),
  // matching iPhone SE 2022 (375pt) and most narrow devices while
  // keeping iPad portrait (744pt) on the desktop popover.
  const [colPickerPos, setColPickerPos] = useState({ top: 0, left: 0 });
  const [colPickerMobile, setColPickerMobile] = useState(false);
  const colPickerBtnRef = useRef(null);
  // v1.0-pre: Export dropdown menu (full / emails-only)
  const [showExportMenu, setShowExportMenu] = useState(false);
  const exportMenuBtnRef = useRef(null);
  const [markModal, setMarkModal] = useState(null);
  // v0.70d-3c-10: message viewer modal. State holds {name, message}
  // when open, null when closed. Triggered by clicking the message
  // cell in either the desktop table or the mobile card view (both
  // go through the same renderCell path).
  const [messageModal, setMessageModal] = useState(null);
  const { defs: markDefs, assignments: markAssignments, getParticipantMarks, assign: assignMark, unassign: unassignMark } = useMarks(eventId);

  // v0.50f-4: download the participants CSV. Same endpoint used by the
  // Setup > Export admin section; surfaced here as a quick action next
  // to Import. Backend now emits GDPR Consent + all custom-field columns
  // so the CSV round-trips through the lenient importer.
  const handleDownloadCSV = (mode = 'full') => {
    setShowExportMenu(false);
    const url = `/api/events/${eventId}/export/participants.csv${mode === 'emails' ? '?mode=emails' : ''}`;
    const filename = mode === 'emails' ? `emails_${eventId}.csv` : `participants_${eventId}.csv`;
    fetch(url, { headers: { Authorization: `Bearer ${getToken()}` } })
      .then(res => { if (!res.ok) throw new Error('Export failed'); return res.blob(); })
      .then(blob => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = filename;
        a.click();
        URL.revokeObjectURL(a.href);
      })
      .catch(err => console.error('CSV export failed:', err));
  };

  // Custom field definitions (all ever defined for event, incl. removed)
  const [customFieldDefs, setCustomFieldDefs] = useState([]);

  // Inline editing
  const [editingId, setEditingId] = useState(null);
  const [editField, setEditField] = useState(null);
  const [editValues, setEditValues] = useState({});
  // v1.0-pre #2: confirmation modal for field edits. Opens after the user
  // commits an inline edit, shows old → new value, requires explicit
  // confirmation before the API call. Per Johannes's instruction, every
  // field edit on a participant should require a deliberate confirm step.
  const [confirmModal, setConfirmModal] = useState(null);
  // ↑ shape: null when closed; when open: { participant, field, fieldLabel, oldValue, newValue, payload }
  const [statusEditing, setStatusEditing] = useState(null);

  const { formatDate } = useDateFormat();
  const { t, lang } = useI18n();
  const { showToast, ToastHost } = useToast();
  const colLabel = (col) => (col.label.includes('.') ? t(col.label) : col.label);
  const { confirm, ConfirmOverlay } = useConfirmOverlay();

  // v0.73: per-row export busy state. Set of participant IDs whose
  // export is currently in flight; disables the button to prevent
  // duplicate clicks. Cleared on completion (success OR error).
  const [exportingIds, setExportingIds] = useState(new Set());
  // v1.0-pre: per-row resend-confirmation busy state. Same pattern.
  const [resendingIds, setResendingIds] = useState(new Set());
  const handleExportParticipant = async (p) => {
    if (!p || !eventId || exportingIds.has(p.id)) return;
    setExportingIds(prev => new Set(prev).add(p.id));
    try {
      await downloadParticipantDataExport({
        eventId,
        participantId: p.id,
        token: getToken(),
      });
      showToast(
        t('people.export.success', { name: `${p.first_name} ${p.last_name}` }),
        'success'
      );
    } catch (err) {
      const fallbackErr = err?.i18nKey || err?.friendlyKey ? err : new Error(t('people.export.error'));
      showToast(fallbackErr, 'error');
    } finally {
      setExportingIds(prev => {
        const next = new Set(prev);
        next.delete(p.id);
        return next;
      });
    }
  };

  const handleResendConfirmation = async (p) => {
    if (!p || !eventId || resendingIds.has(p.id)) return;
    if (p.registration_status === 'cancelled') {
      showToast(new Error(t('errors.participant.cancelled_no_resend')), 'error');
      return;
    }
    setResendingIds(prev => new Set(prev).add(p.id));
    try {
      const res = await fetch(
        `/api/events/${eventId}/participants/${p.id}/resend-confirmation`,
        { method: 'POST', headers: { Authorization: `Bearer ${getToken()}` } }
      );
      if (!res.ok) {
        let payload = null;
        try { payload = await res.json(); } catch (_) { /* ignore */ }
        const key = payload?.detail?.key;
        if (key) throw Object.assign(new Error('Resend failed'), { i18nKey: key });
        throw new Error(t('people.resend.error'));
      }
      showToast(
        t('people.resend.success', { name: `${p.first_name} ${p.last_name}` }),
        'success'
      );
    } catch (err) {
      const fallbackErr = err?.i18nKey || err?.friendlyKey ? err : new Error(t('people.resend.error'));
      showToast(fallbackErr, 'error');
    } finally {
      setResendingIds(prev => {
        const next = new Set(prev);
        next.delete(p.id);
        return next;
      });
    }
  };

  useEffect(() => {
    if (!eventId) return;
    cfApi.list(eventId).then(setCustomFieldDefs).catch(() => {});
  }, [eventId]);

  // Build available columns: built-ins that have data + all custom fields
  const availableColumns = useMemo(() => {
    const dataFieldIds = new Set();
    participantList.forEach(p => {
      BUILTIN_COLUMNS.forEach(col => {
        if (col.field && p[col.field]) dataFieldIds.add(col.id);
      });
    });

    const builtins = BUILTIN_COLUMNS.filter(col =>
      col.always || col.default || !col.field || dataFieldIds.has(col.id)
    );

    const customs = customFieldDefs.map(cf => ({
      id: `cf_${cf.id}`,
      label: cf.label,
      cfId: cf.id,
      isCustom: true,
    }));

    return [...builtins, ...customs];
  }, [participantList, customFieldDefs]);

  // Open column picker at fixed screen position
  // v0.70d-3c-10a: switched from right-anchored to left-anchored
  // with viewport clamping. Pre-3c-10a, on narrow viewports
  // (iPhone) the "Columns" button sits near the left edge, so
  // right-anchoring (`right: window.innerWidth - rect.right`)
  // pushed the popover's left edge off-screen — only the right
  // few pixels were visible, making column toggles unreachable
  // on mobile. Now: try to align the popover's right edge with
  // the button's right edge, but clamp left within the viewport
  // with an 8px margin on each side. POPOVER_WIDTH is an estimate
  // (min-w-[220px] + ~20px chrome + headroom for German labels);
  // bumped from 240 → 280 in the 3c-10a follow-up to cover the
  // longest realistic column labels ("Kirche / Organisation",
  // "Geburtsdatum", and typical custom-field labels under
  // ~32 chars). If a user defines an exceptionally long custom
  // field label that pushes the popover wider than 280, it may
  // clip slightly at the right edge — still better than
  // disappearing off the left, and the symmetric clamping
  // protects the right-edge case too (button near right of
  // viewport places popover further left automatically).
  // v0.70d-3c-12: hybrid mode — under the SM breakpoint (640px)
  // we switch entirely to a centred modal with backdrop. The
  // viewport-clamped popover was navigable on iPhone SE but
  // still felt cramped; the modal is the native-feeling pattern
  // and gives the column toggles room to breathe. Above 640px,
  // the existing popover behaviour is preserved unchanged.
  const openColPicker = () => {
    const isMobile = typeof window !== 'undefined' && window.innerWidth < 640;
    setColPickerMobile(isMobile);
    if (!isMobile && colPickerBtnRef.current) {
      const rect = colPickerBtnRef.current.getBoundingClientRect();
      const POPOVER_WIDTH = 280;
      const MARGIN = 8;
      // Desired: popover's right edge aligned with button's right edge
      let desiredLeft = rect.right - POPOVER_WIDTH;
      // Clamp: keep within [MARGIN, viewport - POPOVER_WIDTH - MARGIN]
      const maxLeft = Math.max(MARGIN, window.innerWidth - POPOVER_WIDTH - MARGIN);
      desiredLeft = Math.max(MARGIN, Math.min(desiredLeft, maxLeft));
      setColPickerPos({ top: rect.bottom + 6, left: desiredLeft });
    }
    setShowColPicker(v => !v);
  };

  useEffect(() => {
    if (!showColPicker || colPickerMobile) return;
    // v0.70d-3c-12: only attach the document-level click-outside
    // dismiss for the popover variant. The mobile modal has its own
    // backdrop click-handler, and attaching a document-level listener
    // there would compete with it.
    const handler = (e) => {
      if (!e.target.closest('[data-col-picker]') && !colPickerBtnRef.current?.contains(e.target)) {
        setShowColPicker(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showColPicker, colPickerMobile]);

  const handleSort = (col) => {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortCol(col); setSortDir('asc'); }
  };

  const sortArrow = (col) => {
    if (sortCol !== col) return <span className="ml-0.5" style={{ color: 'var(--text-subtle)', opacity: 0.5 }}>↕</span>;
    return <span className="text-steel-blue ml-0.5">{sortDir === 'asc' ? '↑' : '↓'}</span>;
  };

  const filtered = useMemo(() => {
    let list = [...participantList];
    if (search) {
      const q = search.toLowerCase();
      // Check if query matches any mark name
      const matchingMarkIds = new Set(
        markDefs.filter(m => m.name.toLowerCase().includes(q)).map(m => String(m.id))
      );
      list = list.filter(p => {
        if (`${p.first_name} ${p.last_name}`.toLowerCase().includes(q)) return true;
        if (p.email.toLowerCase().includes(q)) return true;
        if (p.group_code && p.group_code.toLowerCase().includes(q)) return true;
        if (p.phone && p.phone.toLowerCase().includes(q)) return true;
        if (p.church_organisation && p.church_organisation.toLowerCase().includes(q)) return true;
        // Search by mark name
        if (matchingMarkIds.size > 0) {
          const pMarkIds = new Set((markAssignments[String(p.id)] || []).map(a => String(a.mark_id)));
          if ([...matchingMarkIds].some(id => pMarkIds.has(id))) return true;
        }
        return false;
      });
    }
    if (statusFilter) list = list.filter(p => p.registration_status === statusFilter);
    list.sort((a, b) => {
      // v0.70d-2d-2 (P1): when no status filter is active ("Alle"),
      // push cancelled rows to the end of the default-ordered list.
      // Strike-through on the name (in the row render) telegraphs the
      // state instantly; bottom-of-list placement keeps cancelled rows
      // accessible (for re-activation, audit) without putting them in
      // the everyday flow. When a specific filter IS active, we skip
      // this — the user has explicitly asked for that status.
      if (!statusFilter) {
        const aCancelled = a.registration_status === 'cancelled';
        const bCancelled = b.registration_status === 'cancelled';
        if (aCancelled !== bCancelled) return aCancelled ? 1 : -1;
      }
      let va, vb;
      switch (sortCol) {
        case 'participant_number': va = a.participant_number || 0; vb = b.participant_number || 0; break;
      case 'name': va = `${a.first_name} ${a.last_name}`; vb = `${b.first_name} ${b.last_name}`; break;
        case 'email': va = a.email; vb = b.email; break;
        case 'group_code': va = a.group_code || ''; vb = b.group_code || ''; break;
        case 'status': va = a.registration_status; vb = b.registration_status; break;
        case 'gender': va = a.gender || ''; vb = b.gender || ''; break;
        case 'date_of_birth': va = a.date_of_birth || ''; vb = b.date_of_birth || ''; break;
        case 'registered_at': va = a.created_at || ''; vb = b.created_at || ''; break;
        case 'checked_in': va = a.checked_in ? '1' : '0'; vb = b.checked_in ? '1' : '0'; break;
        case 'country': va = a.country || ''; vb = b.country || ''; break;
        case 'church_organisation': va = a.church_organisation || ''; vb = b.church_organisation || ''; break;
        default: va = ''; vb = '';
      }
      if (typeof va === 'string') { va = va.toLowerCase(); vb = vb.toLowerCase(); }
      if (va < vb) return sortDir === 'asc' ? -1 : 1;
      if (va > vb) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return list;
  }, [participantList, search, statusFilter, sortCol, sortDir, markDefs, markAssignments]);

  const startEdit = async (p, field) => {
    if (!isAdmin) return;
    if (field === 'name' || field === 'email') {
      const ok = await confirm({
        title: `Edit ${field === 'name' ? 'name' : 'email address'}?`,
        message: 'You are about to edit personal data. If a confirmation email was already sent, the participant may have received it at a different address. Please ensure this change is intentional.',
        confirmLabel: 'Edit',
      });
      if (!ok) return;
    }
    setEditingId(p.id);
    setEditField(field);
    setEditValues({ first_name: p.first_name, last_name: p.last_name, email: p.email, group_code: p.group_code || '' });
  };

  const saveEdit = async (participantId) => {
    try {
      const payload = {};
      if (editField === 'name') { payload.first_name = editValues.first_name; payload.last_name = editValues.last_name; }
      else if (editField === 'email') { payload.email = editValues.email; }
      else if (editField === 'group_code') { payload.group_code = editValues.group_code; }
      await participantsApi.update(participantId, payload);
      setEditingId(null); setEditField(null);
      if (onDataChange) onDataChange();
    } catch {}
  };

  const cancelEdit = () => { setEditingId(null); setEditField(null); };

  // v1.0-pre #2: generic-field edit flow.
  //
  // The original inline editor (used for name/email/group_code) auto-saves
  // when the user clicks Save in the inline form, no confirmation step.
  // The new fields go through a different flow: inline editor → click
  // confirm → modal showing old → new → final API call. The two flows
  // coexist; the generic helpers below are only used for fields listed
  // in EDITABLE_FIELDS.

  const startGenericEdit = (p, fieldKey) => {
    if (!isAdmin) return;
    const cfg = EDITABLE_FIELDS[fieldKey];
    if (!cfg) return;
    const current = p[cfg.readField] ?? '';
    setEditingId(p.id);
    setEditField(fieldKey);
    setEditValues({ ...editValues, [fieldKey]: current });
  };

  const requestGenericConfirm = (p, fieldKey) => {
    const cfg = EDITABLE_FIELDS[fieldKey];
    if (!cfg) return;
    const oldValue = p[cfg.readField] ?? '';
    const newValue = editValues[fieldKey] ?? '';
    // No-op: same value, just close the editor without prompting.
    if (String(oldValue) === String(newValue)) {
      cancelEdit();
      return;
    }
    // For display in the modal: humanise the old/new values where they
    // need it (gender translations, date formatting). Keeping the raw
    // values on `payload` so what we send to the API is unchanged.
    let oldDisplay = oldValue, newDisplay = newValue;
    if (fieldKey === 'gender') {
      const tr = (g) => g === 'male' ? t('people.gender.male')
                     : g === 'female' ? t('people.gender.female')
                     : '';
      oldDisplay = tr(oldValue);
      newDisplay = tr(newValue);
    } else if (fieldKey === 'date_of_birth') {
      oldDisplay = oldValue ? formatDate(oldValue) : '';
      newDisplay = newValue ? formatDate(newValue) : '';
    }
    setConfirmModal({
      participant: p,
      field: fieldKey,
      fieldLabel: t(cfg.labelKey),
      oldValue: oldDisplay,
      newValue: newDisplay,
      payload: { [cfg.readField]: newValue === '' ? null : newValue },
    });
  };

  const performGenericSave = async () => {
    if (!confirmModal) return;
    try {
      await participantsApi.update(confirmModal.participant.id, confirmModal.payload);
      setConfirmModal(null);
      setEditingId(null);
      setEditField(null);
      if (onDataChange) onDataChange();
    } catch (err) {
      // Leave the modal open so the user can see the error and retry.
      // The error will surface via the existing TranslatedError host
      // through the parent's reload — for now, close on error too to
      // avoid a stuck modal. v1.0 polish: surface the error inline.
      setConfirmModal(null);
      setEditingId(null);
      setEditField(null);
      if (onDataChange) onDataChange();
    }
  };

  const cancelGenericConfirm = () => {
    setConfirmModal(null);
  };

  // v0.87 #14: parallel edit flow for custom fields. Custom field IDs
  // are arbitrary UUIDs (not in EDITABLE_FIELDS); we key the editing
  // session by 'cf:<uuid>' and look up the field definition each time.
  const startCustomFieldEdit = (p, cfDef) => {
    if (!isAdmin) return;
    const fieldKey = `cf:${cfDef.id}`;
    const current = p.custom_fields?.[cfDef.id] ?? '';
    setEditingId(p.id);
    setEditField(fieldKey);
    setEditValues({ ...editValues, [fieldKey]: current });
  };

  const requestCustomFieldConfirm = (p, cfDef) => {
    const fieldKey = `cf:${cfDef.id}`;
    const oldValue = p.custom_fields?.[cfDef.id] ?? '';
    const newValue = editValues[fieldKey] ?? '';
    if (String(oldValue) === String(newValue)) {
      cancelEdit();
      return;
    }
    // Display: select fields show the choice label; date fields format.
    let oldDisplay = oldValue, newDisplay = newValue;
    if (cfDef.field_type === 'date') {
      oldDisplay = oldValue ? formatDate(oldValue) : '';
      newDisplay = newValue ? formatDate(newValue) : '';
    }
    setConfirmModal({
      participant: p,
      field: fieldKey,
      fieldLabel: cfDef.label,
      oldValue: oldDisplay,
      newValue: newDisplay,
      // v0.87 #14: PATCH /participants/{id} with custom_fields object
      // is upserted server-side (see participant_service.update_participant).
      // Empty string = clear the field; null also accepted by backend.
      payload: { custom_fields: { [cfDef.id]: newValue === '' ? null : String(newValue) } },
    });
  };

  const handleStatusChange = async (participantId, newStatus) => {
    try {
      await participantsApi.update(participantId, { registration_status: newStatus });
      setStatusEditing(null);
      if (onDataChange) onDataChange();
    } catch {}
  };

  const toggleCol = (colId) => {
    const next = new Set(visibleCols);
    if (next.has(colId)) next.delete(colId); else next.add(colId);
    setVisibleCols(next);
    if (colsStorageKey) {
      try { localStorage.setItem(colsStorageKey, JSON.stringify([...next])); } catch {}
    }
  };

  const handleColDrop = (dragId, dropId) => {
    if (dragId === dropId || dragId === 'participant_number' || dropId === 'participant_number') return;
    // Build a fresh order from current activeColumns (excluding participant_number)
    const current = activeColumns.filter(c => c.id !== 'participant_number').map(c => c.id);
    const from = current.indexOf(dragId);
    const to = current.indexOf(dropId);
    if (from === -1 || to === -1) return;
    const next = [...current];
    next.splice(from, 1);
    next.splice(to, 0, dragId);
    setColOrder(next);
    if (colOrderKey) {
      try { localStorage.setItem(colOrderKey, JSON.stringify(next)); } catch {}
    }
    setDragColId(null);
  };

  const getNoteCount = (pid) => noteCounts?.[`participant:${pid}`] || 0;
  // v0.50d-5g: theme-aware inline-edit input — bg/border/text from CSS vars.
  const inputClass = "rounded border bg-[var(--app-bg)] border-[var(--io-accent)] text-[var(--text-primary)] px-1.5 py-0.5 text-xs focus:outline-none w-full";

  // v0.50d-5g / v0.70d-2a (R8a/R8c): theme-aware status pill tuples
  // (bg + color), used inline. Semantic mapping:
  //   pending   → pending-tint (organiser is awaiting confirmation)
  //   confirmed → accent-tint (registration is complete / active)
  //   cancelled → alert-tint (user withdrew — burgundy)
  const STATUS_PILL = {
    pending:   { bg: 'var(--pending-tint)', color: 'var(--pending-color)' },
    confirmed: { bg: 'var(--accent-tint)',  color: 'var(--io-accent)' },
    cancelled: { bg: 'var(--alert-tint)',   color: 'var(--alert-burgundy)' },
  };

  // v0.87 #14: helper that renders a custom-field cell as click-to-edit
  // view, inline editor matched to the field's type, then confirm modal
  // on save. Mirrors renderEditableField but reads cfDef metadata
  // instead of EDITABLE_FIELDS.
  const renderEditableCustomField = (p, cfDef) => {
    const fieldKey = `cf:${cfDef.id}`;
    const canEdit = isAdmin;
    const editing = editingId === p.id && editField === fieldKey;
    const currentDisplay = p.custom_fields?.[cfDef.id];

    if (!editing) {
      // Show value, or em-dash if empty. Boolean → tick/cross. Select →
      // raw choice label. Date → formatted via formatDate.
      let displayNode;
      if (currentDisplay === undefined || currentDisplay === null || currentDisplay === '') {
        displayNode = <span style={{ color: 'var(--text-subtle)' }}>—</span>;
      } else if (cfDef.field_type === 'boolean') {
        const truthy = String(currentDisplay).toLowerCase() === 'true' || currentDisplay === '1';
        displayNode = <span>{truthy ? '✓' : '✕'}</span>;
      } else if (cfDef.field_type === 'date') {
        displayNode = <span>{formatDate(currentDisplay)}</span>;
      } else {
        displayNode = <span>{currentDisplay}</span>;
      }
      const wrapperClass = canEdit
        ? "cursor-pointer hover:underline decoration-dotted underline-offset-2 text-xs"
        : "text-xs";
      return (
        <span
          className={wrapperClass}
          style={{ color: 'var(--text-muted)' }}
          onClick={canEdit ? () => startCustomFieldEdit(p, cfDef) : undefined}
          title={canEdit ? t('people.edit.click_to_edit') : undefined}
        >
          {displayNode}
        </span>
      );
    }

    // Editing — input matched to the field type.
    const value = editValues[fieldKey] ?? '';
    const setValue = (v) => setEditValues(ev => ({ ...ev, [fieldKey]: v }));
    const onKeyDown = (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        requestCustomFieldConfirm(p, cfDef);
      } else if (e.key === 'Escape') {
        e.preventDefault();
        cancelEdit();
      }
    };
    let inputEl;
    if (cfDef.field_type === 'select' && cfDef.options?.choices) {
      inputEl = (
        <select autoFocus value={value} onChange={e => setValue(e.target.value)} onKeyDown={onKeyDown}
          className="text-xs px-2 py-1 rounded border w-full"
          style={{ background: 'var(--app-bg)', borderColor: 'var(--card-border)', color: 'var(--text-primary)' }}>
          <option value="">{t('common.none')}</option>
          {cfDef.options.choices.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      );
    } else if (cfDef.field_type === 'boolean') {
      inputEl = (
        <select autoFocus value={value} onChange={e => setValue(e.target.value)} onKeyDown={onKeyDown}
          className="text-xs px-2 py-1 rounded border w-full"
          style={{ background: 'var(--app-bg)', borderColor: 'var(--card-border)', color: 'var(--text-primary)' }}>
          <option value="">{t('common.none')}</option>
          <option value="true">✓</option>
          <option value="false">✕</option>
        </select>
      );
    } else {
      const inputType = cfDef.field_type === 'date' ? 'date'
                      : cfDef.field_type === 'number' ? 'number'
                      : 'text';
      inputEl = (
        <input
          autoFocus
          type={inputType}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          className="text-xs px-2 py-1 rounded border w-full"
          style={{ background: 'var(--app-bg)', borderColor: 'var(--card-border)', color: 'var(--text-primary)' }}
        />
      );
    }
    return (
      <div className="flex items-center gap-1 min-w-[140px]">
        {inputEl}
        <button type="button" onClick={() => requestCustomFieldConfirm(p, cfDef)}
          title={t('common.save')}
          className="text-xs px-1.5 py-1 rounded hover:bg-black/5 dark:hover:bg-white/10"
          style={{ color: 'var(--io-accent)' }}>✓</button>
        <button type="button" onClick={cancelEdit}
          title={t('common.cancel')}
          className="text-xs px-1.5 py-1 rounded hover:bg-black/5 dark:hover:bg-white/10"
          style={{ color: 'var(--text-muted)' }}>✕</button>
      </div>
    );
  };

  // v1.0-pre #2: helper that renders a single EDITABLE_FIELDS cell as
  // either a click-to-edit view, an inline editor (when editingId/editField
  // match this row+field), or — once the user clicks Confirm in the
  // editor — opens the ConfirmEditModal via requestGenericConfirm.
  // Returns a JSX node; callers in renderCell route to here for the
  // generic field set.
  const renderEditableField = (p, fieldKey, displayNode) => {
    const cfg = EDITABLE_FIELDS[fieldKey];
    const canEdit = isAdmin && cfg;
    const editing = editingId === p.id && editField === fieldKey;
    if (!editing) {
      const wrapperClass = canEdit
        ? "cursor-pointer hover:underline decoration-dotted underline-offset-2"
        : "";
      return (
        <span
          className={wrapperClass}
          style={canEdit ? { color: 'var(--text-muted)' } : undefined}
          onClick={canEdit ? () => startGenericEdit(p, fieldKey) : undefined}
          title={canEdit ? t('people.edit.click_to_edit') : undefined}
        >
          {displayNode}
        </span>
      );
    }
    // Editing mode — inline input matched to the field's input type.
    const value = editValues[fieldKey] ?? '';
    const setValue = (v) => setEditValues(ev => ({ ...ev, [fieldKey]: v }));
    const onKeyDown = (e) => {
      if (e.key === 'Enter' && cfg.inputType !== 'textarea') {
        e.preventDefault();
        requestGenericConfirm(p, fieldKey);
      } else if (e.key === 'Escape') {
        e.preventDefault();
        cancelEdit();
      }
    };
    let inputEl;
    if (cfg.inputType === 'select') {
      inputEl = (
        <select autoFocus value={value} onChange={e => setValue(e.target.value)} onKeyDown={onKeyDown}
          className="text-xs px-2 py-1 rounded border w-full"
          style={{ background: 'var(--app-bg)', borderColor: 'var(--card-border)', color: 'var(--text-primary)' }}>
          {cfg.options.map(opt => (
            <option key={opt.value} value={opt.value}>{t(opt.labelKey)}</option>
          ))}
        </select>
      );
    } else if (cfg.inputType === 'textarea') {
      inputEl = (
        <textarea autoFocus value={value} onChange={e => setValue(e.target.value)} onKeyDown={onKeyDown}
          rows={3}
          className="text-xs px-2 py-1 rounded border w-full resize-none"
          style={{ background: 'var(--app-bg)', borderColor: 'var(--card-border)', color: 'var(--text-primary)' }}/>
      );
    } else {
      inputEl = (
        <input
          autoFocus
          type={cfg.inputType}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          className="text-xs px-2 py-1 rounded border w-full"
          style={{ background: 'var(--app-bg)', borderColor: 'var(--card-border)', color: 'var(--text-primary)' }}
        />
      );
    }
    return (
      <div className="flex items-center gap-1 min-w-[140px]">
        {inputEl}
        <button type="button" onClick={() => requestGenericConfirm(p, fieldKey)}
          title={t('common.save')}
          className="text-xs px-1.5 py-1 rounded hover:bg-black/5 dark:hover:bg-white/10"
          style={{ color: 'var(--io-accent)' }}>✓</button>
        <button type="button" onClick={cancelEdit}
          title={t('common.cancel')}
          className="text-xs px-1.5 py-1 rounded hover:bg-black/5 dark:hover:bg-white/10"
          style={{ color: 'var(--text-muted)' }}>✕</button>
      </div>
    );
  };

  const renderCell = (p, col) => {
    const isEditing = editingId === p.id;

    if (col.isCustom) {
      // v0.87 #14: route through the editable helper. cfDef lookup is
      // O(n) on customFieldDefs but n is small (≤ event's custom-field
      // count, typically <20). Falls back to the legacy read-only view
      // if the def has gone missing (race during a delete).
      const cfDef = customFieldDefs.find(cf => cf.id === col.cfId);
      if (!cfDef) {
        const val = p.custom_fields?.[col.cfId];
        return <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{val || '—'}</span>;
      }
      return renderEditableCustomField(p, cfDef);
    }

    switch (col.id) {
      case 'participant_number':
        return <span className="font-mono text-xs" style={{ color: 'var(--text-subtle)' }}>#{p.participant_number || '—'}</span>;
      case 'name':
        if (isEditing && editField === 'name') {
          return (
            <div className="flex gap-1 items-center">
              <input value={editValues.first_name} onChange={e => setEditValues(v => ({ ...v, first_name: e.target.value }))}
                onKeyDown={e => { if (e.key === 'Enter') saveEdit(p.id); if (e.key === 'Escape') cancelEdit(); }}
                className={inputClass} style={{ width: '80px' }} autoFocus placeholder="First" />
              <input value={editValues.last_name} onChange={e => setEditValues(v => ({ ...v, last_name: e.target.value }))}
                onKeyDown={e => { if (e.key === 'Enter') saveEdit(p.id); if (e.key === 'Escape') cancelEdit(); }}
                className={inputClass} style={{ width: '80px' }} placeholder="Last" />
              <button onClick={() => saveEdit(p.id)} className="text-[10px] font-semibold shrink-0" style={{ color: 'var(--io-accent)' }}>✓</button>
              <button onClick={cancelEdit} className="text-[10px] shrink-0" style={{ color: 'var(--text-subtle)' }}>✕</button>
            </div>
          );
        }
        {
          const pMarks = getParticipantMarks(p.id, 'people');
          const isCancelled = p.registration_status === 'cancelled';
          return (
            <span className="flex items-center gap-1">
              <span onClick={() => startEdit(p, 'name')}
                className={`font-medium ${isAdmin ? 'cursor-pointer hover:underline' : ''} ${isCancelled ? 'line-through' : ''}`}
                style={{ color: 'var(--text-primary)' }}>
                {p.first_name} {p.last_name}
              </span>
              <MarkDots marksForParticipant={pMarks} onManage={() => setMarkModal(p)} />
            </span>
          );
        }

      case 'email':
        if (isEditing && editField === 'email') {
          return (
            <div className="flex gap-1 items-center">
              <input value={editValues.email} onChange={e => setEditValues(v => ({ ...v, email: e.target.value }))}
                onKeyDown={e => { if (e.key === 'Enter') saveEdit(p.id); if (e.key === 'Escape') cancelEdit(); }}
                className={inputClass} style={{ width: '180px' }} autoFocus type="email" />
              <button onClick={() => saveEdit(p.id)} className="text-[10px] font-semibold shrink-0" style={{ color: 'var(--io-accent)' }}>✓</button>
              <button onClick={cancelEdit} className="text-[10px] shrink-0" style={{ color: 'var(--text-subtle)' }}>✕</button>
            </div>
          );
        }
        return (
          <span onClick={() => startEdit(p, 'email')}
            className={`text-xs ${isAdmin ? 'cursor-pointer hover:underline' : ''}`}
            style={{ color: 'var(--text-muted)' }}>
            {p.email}
          </span>
        );

      case 'group_code':
        if (isEditing && editField === 'group_code') {
          return (
            <div className="flex gap-1 items-center">
              <input value={editValues.group_code} onChange={e => setEditValues(v => ({ ...v, group_code: e.target.value }))}
                onKeyDown={e => { if (e.key === 'Enter') saveEdit(p.id); if (e.key === 'Escape') cancelEdit(); }}
                className={`font-mono ${inputClass}`} style={{ width: '100px' }} autoFocus />
              <button onClick={() => saveEdit(p.id)} className="text-[10px] font-semibold shrink-0" style={{ color: 'var(--io-accent)' }}>✓</button>
              <button onClick={cancelEdit} className="text-[10px] shrink-0" style={{ color: 'var(--text-subtle)' }}>✕</button>
            </div>
          );
        }
        return p.group_code ? (
          <GroupCodeTooltip
            code={p.group_code}
            participants={participantList}
            selfId={p.id}
            t={t}
            lang={lang}
          >
            <span onClick={() => { if (isAdmin) { setEditingId(p.id); setEditField('group_code'); setEditValues(v => ({ ...v, group_code: p.group_code })); } }}
              className={`font-mono text-xs px-1.5 py-0.5 rounded ${isAdmin ? 'cursor-pointer' : ''}`}
              style={{ background: 'rgba(128,128,128,0.12)', color: 'var(--text-primary)' }}>
              {p.group_code}
            </span>
          </GroupCodeTooltip>
        ) : (
          <span onClick={() => { if (isAdmin) { setEditingId(p.id); setEditField('group_code'); setEditValues(v => ({ ...v, group_code: '' })); } }}
            className={`text-xs ${isAdmin ? 'cursor-pointer hover:underline' : ''}`}
            style={{ color: 'var(--text-subtle)' }}>
            {isAdmin ? '+ Add' : '—'}
          </span>
        );

      case 'status': {
        const pill = STATUS_PILL[p.registration_status] || STATUS_PILL.pending;
        if (isAdmin && statusEditing === p.id) {
          return (
            <div className="flex gap-1 flex-wrap">
              {ALL_STATUSES.map(s => {
                const sp = STATUS_PILL[s];
                const active = s === p.registration_status;
                return (
                  <button key={s} onClick={() => handleStatusChange(p.id, s)}
                    className="text-[10px] font-semibold px-1.5 py-0.5 rounded"
                    style={active
                      ? { background: sp.bg, color: sp.color }
                      : { background: 'transparent', color: 'var(--text-subtle)', border: '1px solid var(--card-border)' }}>
                    {t(STATUS_LABELS_KEYS[s] || s)}
                  </button>
                );
              })}
              <button onClick={() => setStatusEditing(null)} className="text-[10px] ml-1" style={{ color: 'var(--text-subtle)' }}>✕</button>
            </div>
          );
        }
        return (
          <button onClick={() => isAdmin && setStatusEditing(p.id)}
            className={`text-xs font-semibold px-1.5 py-0.5 rounded ${isAdmin ? 'cursor-pointer hover:ring-1' : ''}`}
            style={{ background: pill.bg, color: pill.color }}>
            {t(STATUS_LABELS_KEYS[p.registration_status] || p.registration_status)}
          </button>
        );
      }

      case 'gender':
        return renderEditableField(p, 'gender',
          <span style={{ color: 'var(--text-muted)' }}>
            {p.gender ? (p.gender === 'male' ? t('people.gender.male') : t('people.gender.female')) : '—'}
          </span>);
      case 'date_of_birth':
        return renderEditableField(p, 'date_of_birth',
          <span style={{ color: 'var(--text-muted)' }}>
            {p.date_of_birth ? formatDate(p.date_of_birth) : '—'}
          </span>);
      case 'phone':
        return renderEditableField(p, 'phone',
          <span style={{ color: 'var(--text-muted)' }}>{p.phone || '—'}</span>);
      case 'address':
        return renderEditableField(p, 'address',
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{p.address || '—'}</span>);
      case 'country':
        return renderEditableField(p, 'country',
          <span style={{ color: 'var(--text-muted)' }}>{p.country || '—'}</span>);
      case 'church_organisation':
        return renderEditableField(p, 'church_organisation',
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{p.church_organisation || '—'}</span>);
      case 'message':
        // v0.70d-3c-9: messages can be long; show as a click indicator
        // (chat-bubble icon + label) rather than truncated inline text
        // that takes up column space.
        // v0.70d-3c-10: hover-only `title` doesn't work on touch
        // devices, so the cell is now a button. Title preserved (with
        // a ~200-char preview to keep tooltips readable for long
        // messages); click opens MessageViewerModal with the full
        // text. Same change covers desktop and mobile card view —
        // both viewports route through this renderCell branch.
        // v1.0-pre #13: message is the participant's message TO the
        // organisers — read-only, never inline-editable.
        if (!p.message) return <span className="text-xs" style={{ color: 'var(--text-subtle)' }}>—</span>;
        return (
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); setMessageModal({ name: `${p.first_name} ${p.last_name}`, message: p.message, participantId: p.id }); }}
            className="inline-flex items-center gap-1 text-xs hover:underline cursor-pointer"
            style={{ color: 'var(--io-accent)' }}
            title={p.message.length > 200 ? p.message.slice(0, 200) + '…' : p.message}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            <span className="font-semibold">{t('people.message.has_message')}</span>
          </button>
        );
      case 'registered_at':
        return <span className="text-xs" style={{ color: 'var(--text-subtle)' }}>{p.created_at ? new Date(p.created_at).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' }) : '—'}</span>;
      case 'checked_in':
        return p.checked_in
          ? <span className="text-xs font-semibold" style={{ color: 'var(--io-accent)' }}>✓ {p.checked_in_at ? new Date(p.checked_in_at).toLocaleString(undefined, { timeStyle: 'short' }) : ''}</span>
          : <span style={{ color: 'var(--text-subtle)' }}>—</span>;
      case 'notes': {
        const nc = getNoteCount(p.id);
        return (
          <button onClick={() => onOpenNotes && onOpenNotes(p)}
            className="text-xs hover:underline"
            style={{ color: 'var(--io-accent)' }}>
            {t('common.notes')}{nc > 0 && (
              <span className="ml-0.5 text-[8px] px-1 py-0 rounded-full"
                style={{
                  background: 'var(--io-accent)',
                  color: 'var(--card-bg-solid)',
                }}>
                {nc}
              </span>
            )}
          </button>
        );
      }
      default: return '—';
    }
  };

  // Build ordered active columns: participant_number always first, rest follow user colOrder
  const activeColumns = useMemo(() => {
    const visible = availableColumns.filter(c => visibleCols.has(c.id));
    const pnCol = visible.find(c => c.id === 'participant_number');
    const rest = visible.filter(c => c.id !== 'participant_number');
    // Apply user order to rest
    if (colOrder.length > 0) {
      rest.sort((a, b) => {
        const ai = colOrder.indexOf(a.id);
        const bi = colOrder.indexOf(b.id);
        if (ai === -1 && bi === -1) return 0;
        if (ai === -1) return 1;
        if (bi === -1) return -1;
        return ai - bi;
      });
    }
    return pnCol ? [pnCol, ...rest] : rest;
  }, [availableColumns, visibleCols, colOrder]);

  return (
    <div
      className="card-surface-solid rounded-2xl overflow-hidden"
      style={{ border: '1px solid var(--card-border)' }}
    >
      {/* Toolbar */}
      <div className="px-4 py-3 space-y-2" style={{ borderBottom: '1px solid var(--card-border)' }}>
        {/* Row 1: Search */}
        <div className="relative">
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder={t('people.search')}
            className="w-full rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] pl-8 pr-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]" />
          <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-sm" style={{ color: 'var(--text-subtle)' }}>🔍</span>
        </div>

        {/* Row 2: Count */}
        <div className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>
          {filtered.length < participantList.length
            ? t('people.count_filtered', { count: filtered.length, total: participantList.length })
            : t('people.count', { count: filtered.length, total: participantList.length })}
          {search && ' (filtered)'}
        </div>

        {/* Row 3: Filter pills + controls, all left */}
        <div className="flex items-center gap-2 flex-wrap">
          {['', ...ALL_STATUSES].map(s => (
            <button key={s} onClick={() => setStatusFilter(statusFilter === s ? '' : s)}
              className={`text-[10px] px-2.5 py-1 rounded-full font-medium transition-colors ${
                statusFilter === s
                  ? 'bg-steel-blue text-white dark:bg-gold dark:text-deep-navy'
                  : 'hover:bg-black/5 dark:hover:bg-white/10'
              }`}
              style={statusFilter === s ? undefined : {
                background: 'rgba(128,128,128,0.10)',
                color: 'var(--text-muted)',
              }}>
              {s === '' ? t('common.all') : t(STATUS_LABELS_KEYS[s] || s)}
            </button>
          ))}
          <button ref={colPickerBtnRef} onClick={openColPicker}
            className="text-xs font-medium px-3 py-1.5 rounded-card border hover:bg-black/5 dark:hover:bg-white/10"
            style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}>
            {t('people.columns')}
          </button>
          {isAdmin && (
            <div className="relative">
              <button ref={exportMenuBtnRef} onClick={() => setShowExportMenu(v => !v)}
                className="text-xs font-medium px-3 py-1.5 rounded-card border hover:bg-black/5 dark:hover:bg-white/10"
                style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}>
                ↓ {t('batch.export')} ▾
              </button>
              {showExportMenu && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowExportMenu(false)} />
                  {/* v1.0-pre #22: card-surface-solid + explicit opaque
                      background. Previous pass used var(--card-bg) which
                      is translucent in this theme; the table beneath was
                      bleeding through and made the menu options hard to
                      read. */}
                  <div className="card-surface-solid absolute right-0 mt-1 z-50 rounded-card border shadow-lg min-w-[260px]"
                    style={{ borderColor: 'var(--card-border)' }}>
                    <button onClick={() => handleDownloadCSV('full')}
                      className="block w-full text-left px-3 py-2.5 text-xs hover:bg-black/5 dark:hover:bg-white/10 rounded-t-card"
                      style={{ color: 'var(--text-primary)' }}>
                      <div className="font-semibold">{t('batch.export.full')}</div>
                      <div className="text-[10px] mt-0.5" style={{ color: 'var(--text-muted)' }}>
                        {t('batch.export.full.hint')}
                      </div>
                    </button>
                    <button onClick={() => handleDownloadCSV('emails')}
                      className="block w-full text-left px-3 py-2.5 text-xs hover:bg-black/5 dark:hover:bg-white/10 border-t rounded-b-card"
                      style={{ color: 'var(--text-primary)', borderColor: 'var(--card-border)' }}>
                      <div className="font-semibold">{t('batch.export.emails')}</div>
                      <div className="text-[10px] mt-0.5" style={{ color: 'var(--text-muted)' }}>
                        {t('batch.export.emails.hint')}
                      </div>
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
          {isAdmin && (
            <button onClick={() => setShowBatch(true)}
              className="text-xs font-medium px-3 py-1.5 rounded-card border hover:bg-black/5 dark:hover:bg-white/10"
              style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}>
              ↑ {t('batch.import_csv')}
            </button>
          )}
        </div>
      </div>

      {/* Column picker — under SM breakpoint renders as a centred
          modal with backdrop; above SM renders as the existing
          fixed-position popover anchored to the Columns button.
          Inner content (the lists) is identical between modes. */}
      {showColPicker && (() => {
        const innerContent = (
          <>
            <p className="text-[9px] uppercase tracking-caps font-semibold mb-2" style={{ color: 'var(--text-subtle)' }}>
              {t('people.show_hide')}
            </p>
            <p className="text-[9px] uppercase tracking-caps mb-1" style={{ color: 'var(--text-subtle)', opacity: 0.7 }}>
              {t('people.columns.builtin')}
            </p>
            {availableColumns.filter(c => !c.isCustom && !c.always).map(col => (
              <label key={col.id} className="flex items-center gap-2 py-0.5 text-xs cursor-pointer"
                style={{ color: 'var(--text-muted)' }}>
                <input type="checkbox" checked={visibleCols.has(col.id)}
                  onChange={() => toggleCol(col.id)}
                  className="h-3 w-3 rounded accent-steel-blue dark:accent-gold" />
                {colLabel(col)}
              </label>
            ))}
            {customFieldDefs.length > 0 && (
              <>
                <p className="text-[9px] uppercase tracking-caps mb-1 mt-3" style={{ color: 'var(--text-subtle)', opacity: 0.7 }}>
                  {t('people.columns.custom')}
                </p>
                {availableColumns.filter(c => c.isCustom).map(col => (
                  <label key={col.id} className="flex items-center gap-2 py-0.5 text-xs cursor-pointer"
                    style={{ color: 'var(--text-muted)' }}>
                    <input type="checkbox" checked={visibleCols.has(col.id)}
                      onChange={() => toggleCol(col.id)}
                      className="h-3 w-3 rounded accent-steel-blue dark:accent-gold" />
                    {colLabel(col)}
                  </label>
                ))}
              </>
            )}
            <button onClick={() => setShowColPicker(false)}
              className="mt-3 text-[10px] hover:underline"
              style={{ color: 'var(--text-subtle)' }}>
              {t('common.close')}
            </button>
          </>
        );

        if (colPickerMobile) {
          // Modal variant: backdrop closes; clicking inside doesn't.
          return (
            <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4"
              onClick={() => setShowColPicker(false)}>
              <div data-col-picker
                className="card-surface-solid rounded-card w-full max-w-sm max-h-[80vh] overflow-y-auto py-3 px-4"
                style={{
                  border: '1px solid var(--card-border)',
                  boxShadow: '0 12px 32px rgba(0,0,0,0.25)',
                }}
                onClick={e => e.stopPropagation()}>
                {innerContent}
              </div>
            </div>
          );
        }

        // Popover variant — existing behaviour, unchanged.
        return (
          <div data-col-picker
            className="card-surface-solid fixed rounded-card z-50 min-w-[220px] max-h-80 overflow-y-auto py-2 px-3"
            style={{
              top: colPickerPos.top, left: colPickerPos.left,
              border: '1px solid var(--card-border)',
              boxShadow: '0 12px 32px rgba(0,0,0,0.25)',
            }}>
            {innerContent}
          </div>
        );
      })()}

      {/* Table */}
      {filtered.length === 0 ? (
        <div className="p-5">
          {participantList.length === 0 ? (
            <EmptyState
              compact
              title={t('people.empty.title')}
              hint={t('people.empty.hint')}
            />
          ) : (
            <EmptyState
              compact
              title={t('people.empty_filtered.title')}
              hint={t('people.empty_filtered.hint')}
            />
          )}
        </div>
      ) : (
        <>
        {/* Desktop table — hidden on mobile.
            v1.0.0p: scroll-within-card. Wrapper now constrains both
            axes: vertical scroll inside the card (sticky thead) plus
            horizontal scroll, so the horizontal scrollbar sits at the
            bottom of the card where it's actually visible — instead
            of 300 rows below the fold. max-h tuned for typical
            chrome (event header + phase strip + filter bar ~= 16rem
            above the table). On exceptionally short viewports the
            inner scroll still works, just with less visible height. */}
        <div className="hidden md:block overflow-auto max-h-[calc(100vh-20rem)]">
          <table className="w-full min-w-max text-sm">
            <thead className="sticky top-0 z-20">
              <tr
                className="text-left text-[10px] uppercase tracking-caps font-semibold"
                style={{
                  background: 'var(--card-bg-solid)',
                  color: 'var(--text-subtle)',
                  borderBottom: '1px solid var(--card-border)',
                  boxShadow: '0 1px 0 var(--card-border)',
                }}>
                {activeColumns.map(col => (
                  <th key={col.id}
                    draggable={col.id !== 'participant_number' && col.id !== 'notes'}
                    onDragStart={() => setDragColId(col.id)}
                    onDragOver={e => { if (dragColId && dragColId !== col.id) e.preventDefault(); }}
                    onDrop={() => { if (dragColId) handleColDrop(dragColId, col.id); }}
                    onDragEnd={() => setDragColId(null)}
                    onClick={() => !['notes'].includes(col.id) && handleSort(col.id)}
                    className={`px-4 py-2 whitespace-nowrap select-none transition-colors ${dragColId === col.id ? 'opacity-40' : ''} ${!['notes'].includes(col.id) ? 'cursor-pointer' : ''} ${col.id === 'notes' ? 'text-center' : ''} ${col.id !== 'participant_number' && col.id !== 'notes' ? 'cursor-move' : ''} ${col.id === 'name' ? 'sticky left-0 z-30' : ''}`}
                    style={col.id === 'name' ? {
                      background: 'var(--card-bg-solid)',
                      boxShadow: '1px 0 0 0 var(--card-border)',
                    } : undefined}>
                    {col.id !== 'participant_number' && col.id !== 'notes' && (
                      <span className="mr-1 text-[10px]" style={{ color: 'var(--text-subtle)', opacity: 0.5 }}>⠿</span>
                    )}
                    {colLabel(col)}{!['notes'].includes(col.id) && sortArrow(col.id)}
                  </th>
                ))}
                {isAdmin && <th className="px-4 py-2 text-right font-semibold">{t('common.actions')}</th>}
              </tr>
            </thead>
            <tbody>
              {filtered.map(p => (
                <tr key={p.id}
                  className={`transition-colors hover:bg-black/[0.02] dark:hover:bg-white/[0.03] ${p.registration_status === 'cancelled' ? 'opacity-50' : ''}`}
                  style={{ borderTop: '1px solid var(--card-border)' }}>
                  {activeColumns.map(col => (
                    <td key={col.id}
                      className={`px-4 py-2 ${col.id === 'notes' ? 'text-center' : ''} ${col.id === 'name' ? 'sticky left-0 z-10' : ''}`}
                      style={col.id === 'name' ? {
                        background: 'var(--card-bg-solid)',
                        boxShadow: '1px 0 0 0 var(--card-border)',
                      } : undefined}>
                      {renderCell(p, col)}
                    </td>
                  ))}
                  {isAdmin && (
                    <td className="px-4 py-2 text-right whitespace-nowrap">
                      {p.registration_status !== 'cancelled' && (
                        <button
                          onClick={() => handleResendConfirmation(p)}
                          disabled={resendingIds.has(p.id)}
                          title={t('people.resend.cta.hint')}
                          aria-label={t('people.resend.cta')}
                          className="text-xs font-semibold hover:underline disabled:opacity-50 mr-3"
                          style={{ color: 'var(--text-muted)' }}>
                          {resendingIds.has(p.id) ? <span className="animate-spin inline-block">⟳</span> : '✉'} {t('people.resend.cta')}
                        </button>
                      )}
                      <button
                        onClick={() => handleExportParticipant(p)}
                        disabled={exportingIds.has(p.id)}
                        title={t('people.export.cta.hint')}
                        aria-label={t('people.export.cta')}
                        className="text-xs font-semibold hover:underline disabled:opacity-50 mr-3"
                        style={{ color: 'var(--text-muted)' }}>
                        {exportingIds.has(p.id) ? <span className="animate-spin inline-block">⟳</span> : '↓'} {t('people.export.cta')}
                      </button>
                      {canDelete && (
                        <button onClick={() => onDelete && onDelete(p.id, `${p.first_name} ${p.last_name}`)}
                          className="text-xs font-semibold hover:underline"
                          style={{ color: 'var(--alert-burgundy)' }}>
                          {t('common.remove')}
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* v0.58g: Mobile card view — parallel to desktop table.
            Preserves every interaction (edit clicks, mark dots, notes,
            status pill, delete) without requiring horizontal scroll.
            Collapse-by-default pattern from CheckInPanel v0.58f-1:
            header row always visible; long-tail fields hide behind
            a "▸ N details" toggle when there's anything to hide. */}
        <div className="md:hidden space-y-2 px-4 py-3">
          {filtered.map(p => {
            const pMarks = getParticipantMarks(p.id, 'people');
            const nc = getNoteCount(p.id);
            const pill = STATUS_PILL[p.registration_status] || STATUS_PILL.pending;
            const expanded = mobileExpandedIds.has(p.id);
            // Build the list of "detail" columns that would render with
            // real data for this participant (everything except name,
            // participant_number, status, notes — those stay in the
            // header / footer areas). If nothing here, no toggle shown.
            const detailCols = activeColumns.filter(col =>
              !['name', 'participant_number', 'status', 'notes'].includes(col.id)
            );
            const detailsWithData = detailCols.filter(col => {
              // Simple presence check per column — matches the dash
              // behaviour of renderCell but wrapped in one place.
              switch (col.id) {
                case 'email': return !!p.email;
                case 'group_code': return !!p.group_code;
                case 'gender': return !!p.gender;
                case 'date_of_birth': return !!p.date_of_birth;
                case 'phone': return !!p.phone;
                case 'address': return !!p.address;
                case 'country': return !!p.country;
                case 'church_organisation': return !!p.church_organisation;
                case 'message': return !!p.message;
                case 'registered_at': return !!p.created_at;
                case 'checked_in': return !!p.checked_in;
                default:
                  // Custom-field columns use `cf_<id>` naming upstream
                  if (col.id.startsWith('cf_')) {
                    const cfId = col.id.slice(3);
                    return !!p.custom_fields?.[cfId];
                  }
                  return false;
              }
            });
            const hasHiddenDetails = detailsWithData.length > 0;

            return (
              <div key={p.id}
                className="rounded-2xl"
                style={{
                  background: 'var(--card-bg-solid)',
                  border: '1px solid var(--card-border)',
                  opacity: p.registration_status === 'cancelled' ? 0.55 : 1,
                  padding: '12px',
                }}>
                {/* Row 1: participant number + name + marks + status pill.
                    v0.61a: name and status pill are tap-to-edit for admins,
                    parity with the desktop table inline editing. Reuses the
                    existing editingId/editField/statusEditing state — no
                    separate mobile edit machinery. */}
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[11px] shrink-0"
                    style={{ color: 'var(--text-subtle)' }}>
                    #{p.participant_number || '—'}
                  </span>
                  {editingId === p.id && editField === 'name' ? (
                    <div className="flex gap-1 items-center flex-1 min-w-0">
                      <input value={editValues.first_name}
                        onChange={e => setEditValues(v => ({ ...v, first_name: e.target.value }))}
                        onKeyDown={e => { if (e.key === 'Enter') saveEdit(p.id); if (e.key === 'Escape') cancelEdit(); }}
                        className={inputClass} style={{ maxWidth: '45%' }} autoFocus placeholder="First" />
                      <input value={editValues.last_name}
                        onChange={e => setEditValues(v => ({ ...v, last_name: e.target.value }))}
                        onKeyDown={e => { if (e.key === 'Enter') saveEdit(p.id); if (e.key === 'Escape') cancelEdit(); }}
                        className={inputClass} style={{ maxWidth: '45%' }} placeholder="Last" />
                      <button onClick={() => saveEdit(p.id)}
                        className="text-sm font-semibold shrink-0 px-1"
                        style={{ color: 'var(--io-accent)' }}>✓</button>
                      <button onClick={cancelEdit}
                        className="text-sm shrink-0 px-1"
                        style={{ color: 'var(--text-subtle)' }}>✕</button>
                    </div>
                  ) : (
                    <span onClick={() => startEdit(p, 'name')}
                      className={`font-medium text-sm truncate min-w-0 flex-1 ${isAdmin ? 'cursor-pointer' : ''} ${p.registration_status === 'cancelled' ? 'line-through' : ''}`}
                      style={{ color: 'var(--text-primary)' }}>
                      {p.first_name} {p.last_name}
                    </span>
                  )}
                  {pMarks.length > 0 && (
                    <MarkDots marksForParticipant={pMarks}
                      onManage={() => setMarkModal(p)} />
                  )}
                  {isAdmin && statusEditing === p.id ? (
                    <div className="flex gap-1 flex-wrap shrink-0">
                      {ALL_STATUSES.map(s => {
                        const sp = STATUS_PILL[s];
                        const active = s === p.registration_status;
                        return (
                          <button key={s} onClick={() => handleStatusChange(p.id, s)}
                            className="text-[10px] font-semibold px-1.5 py-0.5 rounded"
                            style={active
                              ? { background: sp.bg, color: sp.color }
                              : { background: 'transparent', color: 'var(--text-subtle)', border: '1px solid var(--card-border)' }}>
                            {t(STATUS_LABELS_KEYS[s] || s)}
                          </button>
                        );
                      })}
                      <button onClick={() => setStatusEditing(null)}
                        className="text-[10px]"
                        style={{ color: 'var(--text-subtle)' }}>✕</button>
                    </div>
                  ) : (
                    <button
                      onClick={() => isAdmin && setStatusEditing(p.id)}
                      disabled={!isAdmin}
                      className={`text-[10px] font-semibold px-1.5 py-0.5 rounded shrink-0 ${isAdmin ? 'cursor-pointer' : 'cursor-default'}`}
                      style={{ background: pill.bg, color: pill.color }}>
                      {t(STATUS_LABELS_KEYS[p.registration_status] || p.registration_status)}
                    </button>
                  )}
                </div>

                {/* Row 2: email always visible — it's the one detail
                    organisers need at a glance for a person card.
                    v0.61a: tap-to-edit parity with desktop. */}
                {editingId === p.id && editField === 'email' ? (
                  <div className="flex gap-1 items-center mt-1">
                    <input value={editValues.email}
                      onChange={e => setEditValues(v => ({ ...v, email: e.target.value }))}
                      onKeyDown={e => { if (e.key === 'Enter') saveEdit(p.id); if (e.key === 'Escape') cancelEdit(); }}
                      className={inputClass} autoFocus type="email" />
                    <button onClick={() => saveEdit(p.id)}
                      className="text-sm font-semibold shrink-0 px-1"
                      style={{ color: 'var(--io-accent)' }}>✓</button>
                    <button onClick={cancelEdit}
                      className="text-sm shrink-0 px-1"
                      style={{ color: 'var(--text-subtle)' }}>✕</button>
                  </div>
                ) : (
                  p.email && (
                    <p onClick={() => startEdit(p, 'email')}
                      className={`text-xs mt-1 truncate ${isAdmin ? 'cursor-pointer' : ''}`}
                      style={{ color: 'var(--text-muted)' }}>
                      {p.email}
                    </p>
                  )
                )}

                {/* Group code row — v0.61a: tap-to-edit parity with
                    desktop. When missing and admin, show a "+ Add" affordance
                    so the field is discoverable from the mobile card. */}
                {editingId === p.id && editField === 'group_code' ? (
                  <div className="flex gap-1 items-center mt-2">
                    <input value={editValues.group_code}
                      onChange={e => setEditValues(v => ({ ...v, group_code: e.target.value }))}
                      onKeyDown={e => { if (e.key === 'Enter') saveEdit(p.id); if (e.key === 'Escape') cancelEdit(); }}
                      className={`font-mono ${inputClass}`} style={{ maxWidth: '160px' }} autoFocus />
                    <button onClick={() => saveEdit(p.id)}
                      className="text-sm font-semibold shrink-0 px-1"
                      style={{ color: 'var(--io-accent)' }}>✓</button>
                    <button onClick={cancelEdit}
                      className="text-sm shrink-0 px-1"
                      style={{ color: 'var(--text-subtle)' }}>✕</button>
                  </div>
                ) : p.group_code ? (
                  <div className="mt-2">
                    <span
                      onClick={() => { if (isAdmin) { setEditingId(p.id); setEditField('group_code'); setEditValues(v => ({ ...v, group_code: p.group_code })); } }}
                      className={`font-mono text-xs px-1.5 py-0.5 rounded ${isAdmin ? 'cursor-pointer' : ''}`}
                      style={{ background: 'rgba(128,128,128,0.12)', color: 'var(--text-primary)' }}>
                      {p.group_code}
                    </span>
                  </div>
                ) : (
                  isAdmin && (
                    <div className="mt-2">
                      <span
                        onClick={() => { setEditingId(p.id); setEditField('group_code'); setEditValues(v => ({ ...v, group_code: '' })); }}
                        className="text-xs cursor-pointer hover:underline"
                        style={{ color: 'var(--text-subtle)' }}>
                        + Add group code
                      </span>
                    </div>
                  )
                )}

                {/* Collapsed: just the footer row with toggle + notes.
                    v0.58g-1: admins always see a toggle (even when no
                    hidden data) so the delete button inside the
                    expanded section remains reachable for minimal
                    registrations. */}
                {!expanded && (hasHiddenDetails || isAdmin || getNoteCount(p.id) >= 0) && (
                  <div className="flex items-center justify-between mt-3 gap-3">
                    {(hasHiddenDetails || isAdmin) ? (
                      <button
                        onClick={() => toggleMobileExpanded(p.id)}
                        className="text-[11px] hover:underline"
                        style={{ color: 'var(--text-subtle)' }}>
                        ▸ {hasHiddenDetails
                            ? (t('people.show_details', { n: detailsWithData.length }))
                            : (t('common.more'))}
                      </button>
                    ) : <span />}
                    <button onClick={() => onOpenNotes && onOpenNotes(p)}
                      className="text-xs font-semibold hover:underline"
                      style={{ color: 'var(--io-accent)' }}>
                      {t('common.notes')}{nc > 0 && (
                        <span className="ml-1 text-[9px] px-1.5 py-0 rounded-full"
                          style={{ background: 'var(--io-accent)', color: 'var(--card-bg-solid)' }}>
                          {nc}
                        </span>
                      )}
                    </button>
                  </div>
                )}

                {/* Expanded: detail pills + footer */}
                {expanded && (
                  <>
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {detailsWithData.map(col => (
                        <span key={col.id}
                          className="inline-flex items-center gap-1 text-[11px] px-2 py-1 rounded-full"
                          style={{
                            background: 'var(--app-bg)',
                            color: 'var(--text-muted)',
                            border: '1px solid var(--card-border)',
                          }}>
                          <span className="font-semibold"
                            style={{ color: 'var(--text-subtle)' }}>
                            {colLabel(col)}:
                          </span>
                          <span>{renderCell(p, col)}</span>
                        </span>
                      ))}
                    </div>
                    <div className="flex items-center justify-between mt-3 gap-3">
                      <button
                        onClick={() => toggleMobileExpanded(p.id)}
                        className="text-[11px] hover:underline"
                        style={{ color: 'var(--text-subtle)' }}>
                        ▴ {t('people.hide_details')}
                      </button>
                      <button onClick={() => onOpenNotes && onOpenNotes(p)}
                        className="text-xs font-semibold hover:underline"
                        style={{ color: 'var(--io-accent)' }}>
                        {t('common.notes')}{nc > 0 && (
                          <span className="ml-1 text-[9px] px-1.5 py-0 rounded-full"
                            style={{ background: 'var(--io-accent)', color: 'var(--card-bg-solid)' }}>
                            {nc}
                          </span>
                        )}
                      </button>
                    </div>
                    {/* v0.58g-1: Admin delete moved into expanded section
                        only — requires a deliberate expand-then-remove
                        gesture, preventing a careless tap on the main
                        card list from nuking a participant. Divider
                        makes the destructive intent clear.
                        v0.70d-3c-10: gate on canDelete (real admin),
                        not isAdmin (which here means people:write).
                        v0.73: export trigger added (isAdmin gate, separate
                        from canDelete — endpoint is admin-only).  */}
                    {isAdmin && (
                      <div className="mt-3 pt-2 flex justify-end gap-3"
                        style={{ borderTop: '1px solid var(--card-border)' }}>
                        {p.registration_status !== 'cancelled' && (
                          <button
                            onClick={() => handleResendConfirmation(p)}
                            disabled={resendingIds.has(p.id)}
                            title={t('people.resend.cta.hint')}
                            className="text-[10px] font-semibold hover:underline disabled:opacity-50"
                            style={{ color: 'var(--text-muted)' }}>
                            {resendingIds.has(p.id) ? <span className="animate-spin inline-block">⟳</span> : '✉'} {t('people.resend.cta')}
                          </button>
                        )}
                        <button
                          onClick={() => handleExportParticipant(p)}
                          disabled={exportingIds.has(p.id)}
                          title={t('people.export.cta.hint')}
                          className="text-[10px] font-semibold hover:underline disabled:opacity-50"
                          style={{ color: 'var(--text-muted)' }}>
                          {exportingIds.has(p.id) ? <span className="animate-spin inline-block">⟳</span> : '↓'} {t('people.export.cta')}
                        </button>
                        {canDelete && (
                          <button onClick={() => onDelete && onDelete(p.id, `${p.first_name} ${p.last_name}`)}
                            className="text-[10px] font-semibold hover:underline"
                            style={{ color: 'var(--alert-burgundy)' }}>
                            {t('common.remove')}
                          </button>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            );
          })}
        </div>
        </>
      )}

      {showBatch && (
        <BatchRegisterModal
          eventId={eventId}
          onClose={() => setShowBatch(false)}
          onDone={() => { setShowBatch(false); if (onDataChange) onDataChange(); }}
        />
      )}

      <ConfirmOverlay />
      <ToastHost />
      {markModal && (
        <MarkAssignModal
          participant={markModal}
          defs={markDefs}
          assignments={markAssignments}
          onAssign={async (markId, participantId) => { await assignMark(markId, participantId); }}
          onUnassign={async (markId, participantId) => { await unassignMark(markId, participantId); }}
          view="people"
          canAssign={canAssignMarks}
          onClose={() => setMarkModal(null)} />
      )}
      {messageModal && (
        <MessageViewerModal
          participantName={messageModal.name}
          message={messageModal.message}
          onClose={() => setMessageModal(null)} />
      )}
      {/* v1.0-pre #2: confirmation modal for inline field edits.
          Open state lives in `confirmModal` (null = closed). When the
          user clicks Confirm the registered participantsApi.update fires;
          on resolve we close + trigger a parent reload. */}
      <ConfirmEditModal
        open={!!confirmModal}
        fieldLabel={confirmModal?.fieldLabel}
        oldValue={confirmModal?.oldValue}
        newValue={confirmModal?.newValue}
        participantName={confirmModal ? `${confirmModal.participant.first_name} ${confirmModal.participant.last_name}` : ''}
        onConfirm={performGenericSave}
        onCancel={cancelGenericConfirm}
      />
    </div>
  );
}
