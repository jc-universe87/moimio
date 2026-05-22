import { useState, useEffect, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { allocationUnits, allocations as allocApi, notes as notesApi, allocationCategories as catApi, preferenceRequests as prefApi, getToken , formatErrorMessage } from '../services/api';
import NotesModal from './NotesModal';
import MarkDots from './MarkDots';
import MarkAssignModal from './MarkAssignModal';
import InsightPanel from './InsightPanel';
import ReviewSurface from './ReviewSurface';
import CategoryHintsStrip from './CategoryHintsStrip';
import { useI18n } from '../hooks/useI18n';
import { useMarks } from '../hooks/useMarks';
import { useToast } from '../hooks/useToast';
import { useConfirmOverlay } from './ConfirmOverlay';
import { usePrefersReducedMotion } from '../hooks/usePrefersReducedMotion';
import { computeMarkSplits } from '../utils/computeCategoryHints';
import { useEventStream } from '../hooks/useEventStream';

import TranslatedError from './TranslatedError';
const TRUNCATE_LEN = 90;
const truncate = (s) => s && s.length > TRUNCATE_LEN ? s.slice(0, TRUNCATE_LEN) + '…' : s;

// v0.61c-2: pointer-fine detection for drag-to-reorder gates. See
// the matching constant in OrganiseDashboard / GroupTypesEditor for
// the full rationale. The viewport-width-based `isMobileView` state
// below stays as-is for layout decisions (e.g. opening the marks
// modal on tap), but the drag-related gates use HAS_FINE_POINTER
// because viewport ≥768 ≠ "user can drag".
const HAS_FINE_POINTER = typeof window !== 'undefined'
  && typeof window.matchMedia === 'function'
  && window.matchMedia('(hover: hover) and (pointer: fine)').matches;

export default function AllocationBoard({ eventId, eventName, category, allCategories, onSelectCategory, participantList, noteCounts, isAdmin, marksPerm, onDataChange, isOverview, includeNotes, openSettings, onSettingsOpened, triggerSuggestMode, onSuggestTriggered }) {
  // v0.50f-1: mark modal opens for everyone on desktop. Only canAssign is
  // gated by marksPerm. Mobile still suppresses the onManage handler for
  // ergonomics (small hitboxes + finger gestures conflict with drag).
  const canAssignMarks = isAdmin || marksPerm === 'write';
  const [units, setUnits] = useState([]);
  const [allMembers, setAllMembers] = useState({});
  const [showCreate, setShowCreate] = useState(false);
  const [editingUnit, setEditingUnit] = useState(null);
  // v1.0.0q: lightweight inline-rename for unit names. Separate from
  // editingUnit (which opens the full edit form for name + description
  // + capacity + gender_restriction). This one only sets a single
  // field — same UX as the group-type title inline rename: click,
  // type, Enter or blur saves, Esc reverts, empty reverts.
  const [editingUnitRenameId, setEditingUnitRenameId] = useState(null);
  const [unitRenameDraft, setUnitRenameDraft] = useState('');
  const [form, setForm] = useState({ name: '', description: '', capacity: '', gender_restriction: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notesFor, setNotesFor] = useState(null);

  // Inline notes (shown in overview when includeNotes=true, always in board view)
  const [catNotes, setCatNotes] = useState([]);
  const [unitNotes, setUnitNotes] = useState({});

  // Person-first
  const [search, setSearch] = useState('');
  const [genderFilter, setGenderFilter] = useState('');
  const [selectedPeople, setSelectedPeople] = useState(new Set());
  const [assignDropdown, setAssignDropdown] = useState(false);
  const [dragUnitId, setDragUnitId] = useState(null);
  const [dragOverUnitId, setDragOverUnitId] = useState(null);

  // Marks
  const { defs: markDefs, assignments: markAssignments, getParticipantMarks, assign: assignMark, unassign: unassignMark } = useMarks(eventId);
  const [markModal, setMarkModal] = useState(null); // participant object or null
  // v0.58e: Insight panel state — participant object (or null to hide)
  const [insightParticipant, setInsightParticipant] = useState(null);

  // Drag
  const [dragParticipant, setDragParticipant] = useState(null);
  const [dragSource, setDragSource] = useState(null);
  const [dragOverUnit, setDragOverUnit] = useState(null);

  // Toast — v0.70d-1 R2: shared useToast hook replaces the local
  // {toast, setToast, toastTimer} state + inline render block.
  // Native alert() calls throughout this file now route through
  // showToast(msg, 'error').
  const { showToast, ToastHost } = useToast();

  // Layout
  const [isMobileView, setIsMobileView] = useState(() => window.innerWidth < 768);
  const rightPanelRef = useRef(null);
  const leftPanelRef = useRef(null);

  const { confirm, ConfirmOverlay } = useConfirmOverlay();
  const { t, lang } = useI18n();
  const itemLabel = category?.item_label || 'Item';

  // ─── Engine state ───
  const [suggesting, setSuggesting] = useState(false);
  const [proposal, setProposal] = useState(null);
  const [committing, setCommitting] = useState(false);
  const [showEngineSettings, setShowEngineSettings] = useState(false);
  const [prefCount, setPrefCount] = useState(0);
  const engineSettingsRef = useRef(null);

  // v0.50g: direct detailed PDF download from overflow menu (the PII-
  // bearing roster). Compact/sign-in rosters moved to the Reports page.
  const [detailedPdfDownloading, setDetailedPdfDownloading] = useState(false);
  // v0.50t: PDF output language, independent of UI language. Defaults
  // to the current UI lang — a German user's first-ever click downloads
  // in German without any config. Lives in the ⋯ menu above the two
  // Detailed PDF buttons so organisers can quickly re-export in another
  // language for external staff. Session-scoped; resets on each page
  // load so yesterday's selection doesn't surprise today.
  const [pdfLang, setPdfLang] = useState(lang);
  // If the user changes UI language while on this page, follow that
  // (mirrors the ReportsPanel behaviour).
  useEffect(() => { setPdfLang(lang); }, [lang]);
  const PDF_LANG_OPTIONS = [
    { code: 'en',    label: 'English' },
    { code: 'de',    label: 'Deutsch' },
    { code: 'ko',    label: '한국어' },
    { code: 'es',    label: 'Español' },
    { code: 'pt-BR', label: 'Português (BR)' },
    { code: 'fr',    label: 'Français' },
  ];

  const handleDetailedPdfDownload = async (withCover = false) => {
    if (!category) return;
    setDetailedPdfDownloading(true);
    try {
      const params = new URLSearchParams({ format: 'detailed' });
      if (withCover) params.set('with_cover', 'true');
      // v0.50t: PDF language is now selectable in the ⋯ menu via a
      // Language dropdown (above the two Detailed PDF buttons). Defaults
      // to the UI lang so existing one-click behaviour is preserved, but
      // organisers can switch it for specific downloads (e.g. to hand
      // off to staff who read another language).
      params.set('lang', pdfLang);
      const url = `/api/events/${eventId}/export/category/${category.id}/pdf?${params.toString()}`;
      const res = await fetch(url, { headers: { Authorization: `Bearer ${getToken()}` } });
      if (!res.ok) {
        let detail = `HTTP ${res.status}`;
        try { const j = await res.json(); detail = j.detail || detail; } catch (_) {}
        throw new Error(detail);
      }
      const blob = await res.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      // v0.50g-1: filename includes event name + date so downloads are
      // disambiguable in a Downloads folder. Matches the pattern used by
      // the Reports page compact/signin downloads.
      const slug = (s) => (s || 'untitled')
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '_')
        .replace(/^_+|_+$/g, '');
      const today = new Date();
      const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
      const parts = [slug(eventName), slug(category.name), 'detailed', dateStr, slug(pdfLang)].filter(Boolean);
      a.download = `${parts.join('_')}.pdf`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (err) {
      // Backend returns 403 for users without people:read. Surface the
      // detail message so organisers see "Read access to people required"
      // rather than a silent no-op.
      // v0.70d-1 R2: toast replaces alert().
      showToast(err, 'error');
    } finally {
      setDetailedPdfDownloading(false);
    }
  };

  // v0.50p: Unconfirm control moved from the OrganiseDashboard card to
  // live inside the category detail (this component). Keeps the
  // reversal close to the other state controls for a given category
  // and removes the dashboard duplication. State + handler mirror the
  // Confirm flow already in catApi.
  const [unconfirming, setUnconfirming] = useState(false);
  const [unconfirmError, setUnconfirmError] = useState(null);
  const handleUnconfirmCategory = async () => {
    if (!category?.id) return;
    setUnconfirming(true); setUnconfirmError(null);
    try {
      await catApi.unconfirm(eventId, category.id);
      // Parent reloads via onDataChange and sends a fresh category object
      // on the next render, which carries confirmed=false. (Removed the
      // earlier optimistic in-place mutation `category.confirmed = false` —
      // mutating React props is forbidden and was redundant with the reload.)
      if (onDataChange) onDataChange();
    } catch (err) {
      setUnconfirmError(err);
    } finally {
      setUnconfirming(false);
    }
  };

  // v0.70d-2e-3 (AB3): confirm-category handler. Lives here next to
  // un-confirm so both state transitions are colocated in the
  // component that owns the post-allocation surface. Mirrors the
  // existing handler in OrganiseDashboard (line ~104) but is invoked
  // from the AB3 "ready to confirm" CTA on the top progress row.
  const [confirming, setConfirming] = useState(false);
  const [confirmError, setConfirmError] = useState(null);
  const handleConfirmCategory = async () => {
    if (!category?.id) return;
    setConfirming(true); setConfirmError(null);
    try {
      await catApi.confirm(eventId, category.id);
      if (onDataChange) onDataChange();
    } catch (err) {
      setConfirmError(err);
    } finally {
      setConfirming(false);
    }
  };

  const navigate = useNavigate();
  const prefersReducedMotion = usePrefersReducedMotion();

  // Split-button mode picker + overflow menu + manage units
  const [showModePicker, setShowModePicker] = useState(false);
  const [manageUnitsOpen, setManageUnitsOpen] = useState(false);
  const [showOverflowMenu, setShowOverflowMenu] = useState(false);
  const overflowMenuRef = useRef(null);

  // Local mirror of category.settings.engine for optimistic UI updates.
  // Synced from prop when category changes; updated immediately on user action.
  const [localEngineSettings, setLocalEngineSettings] = useState(
    () => category?.settings?.engine || {}
  );

  // Mark drag-and-drop state
  const [dragMarkId, setDragMarkId] = useState(null);
  const [dragOverMarkId, setDragOverMarkId] = useState(null);

  // In overview mode, show notes only when includeNotes is true.
  // In board mode (not overview), always show notes.
  const showNotes = isOverview ? !!includeNotes : true;

  useEffect(() => { loadAll(); }, [eventId, category?.id]);

  // v1.0-pre #9: subscribe to the organise SSE stream and refresh on
  // each incoming event. Debounced to 200ms so a burst of rapid changes
  // (e.g. a remote engine run that publishes once per allocation) only
  // triggers one local refetch.
  //
  // v0.98 #32 fix: call BOTH loadAll() and onDataChange(). All local
  // mutations in this file (assign, move, unassign, engine runs,
  // category mutations etc.) call loadAll() to refresh THIS board's
  // units + allocations, then onDataChange() to refresh the parent's
  // category list. The SSE remote-update path was only calling
  // onDataChange — which reloads the (usually unchanged) category
  // list but leaves the units/allocations on screen stale. That's
  // why cross-device sync looked broken: backend published correctly,
  // SSE delivered bytes correctly, the JS callback fired correctly,
  // but the data on screen was never refetched. See curl trace
  // confirming events reach the wire in real-time — the bug was here.
  const refreshDebounceRef = useRef(null);
  useEventStream({
    eventId,
    surface: 'organise',
    onEvent: (msg) => {
      if (!msg) return;
      // Ignore the initial 'connected' frame — it carries no state
      // change. Any real allocation_changed (or unexpected message
      // type) triggers the debounced refetch.
      if (msg.type === 'connected') return;
      if (refreshDebounceRef.current) clearTimeout(refreshDebounceRef.current);
      refreshDebounceRef.current = setTimeout(() => {
        loadAll();
        if (onDataChange) onDataChange();
      }, 200);
    },
  });

  useEffect(() => {
    if (openSettings) {
      const timer = setTimeout(() => {
        setShowEngineSettings(true);
        if (onSettingsOpened) onSettingsOpened();
      }, 150);
      return () => clearTimeout(timer);
    }
  }, [openSettings]);

  useEffect(() => {
    if (triggerSuggestMode) {
      const timer = setTimeout(() => {
        setShowModePicker(true);
        if (onSuggestTriggered) onSuggestTriggered();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [triggerSuggestMode]);

  useEffect(() => {
    const check = () => setIsMobileView(window.innerWidth < 768);
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  // Match left panel height to right panel on desktop
  useEffect(() => {
    if (isMobileView) return;
    const rightEl = rightPanelRef.current;
    const leftEl = leftPanelRef.current;
    if (!rightEl || !leftEl) return;
    const observer = new ResizeObserver(() => {
      const h = rightEl.offsetHeight;
      if (h > 0) leftEl.style.maxHeight = `${h}px`;
    });
    observer.observe(rightEl);
    return () => observer.disconnect();
  }, [isMobileView, units]);

  // v0.70d-1 R2: local showToast removed — the useToast hook
  // declared above provides the same API with the correct semantic
  // colours (io-accent for success, burgundy for error, card for
  // info). See hooks/useToast.jsx.

  const handleReorderUnits = async (fromId, toId) => {
    if (!fromId || !toId || fromId === toId) return;
    const ids = units.map(u => u.id);
    const from = ids.indexOf(fromId);
    const to = ids.indexOf(toId);
    if (from === -1 || to === -1) return;
    const reordered = [...ids];
    reordered.splice(from, 1);
    reordered.splice(to, 0, fromId);
    setUnits(reordered.map(id => units.find(u => u.id === id)));
    try { await catApi.reorderUnits(eventId, category.id, reordered); }
    catch { loadAll(); }
    setDragUnitId(null); setDragOverUnitId(null);
  };

  const loadAll = async () => {
    if (!category) return;
    try {
      const [u, m] = await Promise.all([
        allocationUnits.list(eventId, category.id),
        allocApi.byCategory(eventId, category.id),
      ]);
      setUnits(u);
      setAllMembers(m);
      loadInlineNotes(u);
    } catch (err) { setError(err); }
    finally { setLoading(false); }
  };

  const loadInlineNotes = async (unitList) => {
    try {
      const cn = await notesApi.list('category', category.id);
      setCatNotes(cn);
    } catch {}
    const noteMap = {};
    for (const unit of (unitList || units)) {
      try {
        const un = await notesApi.list('unit', unit.id);
        if (un.length > 0) noteMap[String(unit.id)] = un;
      } catch {}
    }
    setUnitNotes(noteMap);
  };

  // ─── Engine: load preference count ───
  useEffect(() => {
    if (!eventId) return;
    prefApi.list(eventId).then(data => setPrefCount(data.filter(r => !r.resolved).length)).catch(() => {});
  }, [eventId]);

  // Sync local engine settings from prop when category changes
  useEffect(() => {
    setLocalEngineSettings(category?.settings?.engine || {});
  }, [category?.id, category?.settings]);

  // Close engine settings on outside click
  useEffect(() => {
    if (!showEngineSettings) return;
    const handler = (e) => {
      if (engineSettingsRef.current && !engineSettingsRef.current.contains(e.target)) setShowEngineSettings(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showEngineSettings]);

  useEffect(() => {
    if (!showOverflowMenu) return;
    const handler = (e) => {
      if (overflowMenuRef.current && !overflowMenuRef.current.contains(e.target)) setShowOverflowMenu(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showOverflowMenu]);

  // ─── Engine: suggest ───
  const handleSuggest = async (mode = 'replace') => {
    if (units.length === 0) return;
    setShowModePicker(false);
    setSuggesting(true);
    // v0.73e Q4: await any in-flight settings PATCH so the engine
    // reads the latest persisted settings, not stale ones. The
    // settingPatchInFlight ref is null in the common case; the
    // await is a no-op then. Only the rare toggle-then-immediate-
    // Auto-Allocate sequence pays the brief wait.
    if (settingPatchInFlight.current) {
      try { await settingPatchInFlight.current; } catch { /* error already toasted by handleEngineSettingChange */ }
    }
    try {
      const result = await catApi.suggest(eventId, category.id, mode);
      // v0.70d-1 R2: result.error is an engine-reported soft failure
      // (e.g. "No capacity available"). A toast lets the organiser see
      // the message and keep working; an alert() blocked the page.
      // v0.70d-3c-8: engine errors now bubble through HTTP catch with dict-detail; the dead `result.error` check from pre-3c-2 is removed.
      setProposal({ ...result, units });
    } catch (err) { showToast(err, 'error'); }
    finally { setSuggesting(false); }
  };

  // ─── Engine: commit ───
  const handleCommit = async () => {
    if (!proposal) return;
    setCommitting(true);
    try {
      // v0.60c: forward reasoning payload so the backend writes it
      // into the meta JSONB column of each assign event. Missing fields
      // on older proposal shapes are harmless — the API defaults them.
      await catApi.commit(eventId, category.id, proposal.proposed, {
        placementReasons: proposal.placement_reasons,
        engineRunId: proposal.run_id,
      });
      setProposal(null);
      await loadAll();
      if (onDataChange) onDataChange();
    } catch (err) { showToast(err, 'error'); }
    finally { setCommitting(false); }
  };

  // v0.73e Q4: track in-flight settings PATCH so Auto-Allocate can
  // await it before firing the engine. Pre-fix race: toggle change
  // optimistically updates local state + fires async PATCH; user
  // clicks Auto-Allocate immediately, engine reads stale settings
  // from the DB. Post-fix: handleRunEngine (and friends) await
  // settingPatchInFlight.current to resolve before reading the engine.
  // The ref holds the most-recent PATCH promise, or null when no
  // PATCH is in flight.
  const settingPatchInFlight = useRef(null);

  // ─── Engine: update a single setting (optimistic update + persist) ───
  const handleEngineSettingChange = async (key, value) => {
    // Optimistic UI update — local state changes immediately
    const previousSettings = localEngineSettings;
    const newEngine = { ...localEngineSettings, [key]: value };
    setLocalEngineSettings(newEngine);

    // Persist to backend
    const currentSettings = category?.settings || {};
    const newSettings = { ...currentSettings, engine: newEngine };
    const patchPromise = catApi.update(eventId, category.id, { settings: newSettings });
    settingPatchInFlight.current = patchPromise;
    try {
      await patchPromise;
      // The UI reads from localEngineSettings, which is already updated
      // optimistically above. The parent will eventually re-render with
      // the fresh category prop. (Removed the earlier in-place prop
      // mutation `category.settings = newSettings` — mutating React props
      // is forbidden and nothing in this component reads from category.settings
      // directly.)
    } catch (err) {
      // Revert on error
      setLocalEngineSettings(previousSettings);
      // v0.70d-1 R2: toast replaces alert.
      showToast(err, 'error');
    } finally {
      // Clear the in-flight ref ONLY if we're still the latest PATCH —
      // a fresh setting change might already have replaced us. Compare
      // by reference identity.
      if (settingPatchInFlight.current === patchPromise) {
        settingPatchInFlight.current = null;
      }
    }
  };

  // Read engine settings from local state (NOT prop) so UI updates instantly
  const engineSettings = localEngineSettings;

  // v1.0-pre #23: mark_priorities can be in either of two shapes on disk:
  //   - Legacy: ['uuid1', 'uuid2', ...]
  //   - New:    [{id: 'uuid1', behaviour: 'together'}, ...]
  // We normalise to a list of {id, behaviour} objects for local UI use,
  // and convert back to the same shape on save. Behaviour defaults to
  // the global mark cluster_behaviour (still on MarkDefinition) for
  // entries that don't carry their own.
  const rawPriorities = engineSettings.mark_priorities || [];
  const _markBehaviourFromDef = (mid) => {
    const def = markDefs.find(d => String(d.id) === mid);
    return def?.cluster_behaviour || 'none';
  };
  const activeMarkPriorityList = rawPriorities.map(entry => {
    if (typeof entry === 'string') {
      return { id: entry, behaviour: _markBehaviourFromDef(entry) };
    }
    if (entry && typeof entry === 'object' && entry.id) {
      return { id: String(entry.id), behaviour: entry.behaviour || _markBehaviourFromDef(String(entry.id)) };
    }
    return null;
  }).filter(Boolean);
  const activeMarkPriorities = activeMarkPriorityList.map(e => e.id);  // legacy id-only list for code that expects strings

  // v1.0-pre #24: handler for exclusive_group_codes — this is a
  // top-level field on the category record (not inside settings.engine),
  // so it doesn't ride through handleEngineSettingChange. The engine
  // already reads from this field; we just expose the toggle in the
  // engine-settings popover for parity with the rest of the allocation
  // configuration.
  // v0.83: optimistic local mirror so the checkbox visually reflects
  // the user's click without waiting for the parent re-fetch round-trip.
  // The mirror is null when no override is in flight (read directly from
  // category prop); otherwise it overrides the rendered state.
  const [exclusiveGroupCodesOverride, setExclusiveGroupCodesOverride] = useState(null);
  const exclusiveGroupCodesValue = exclusiveGroupCodesOverride !== null
    ? exclusiveGroupCodesOverride
    : !!category?.exclusive_group_codes;

  const handleExclusiveGroupCodesToggle = async (value) => {
    const previousValue = !!category?.exclusive_group_codes;
    if (previousValue === !!value) return;
    setExclusiveGroupCodesOverride(!!value);
    try {
      await catApi.update(eventId, category.id, { exclusive_group_codes: !!value });
      // Parent re-fetches via onDataChange; once category prop updates,
      // we drop the override (handled in the useEffect below).
      if (onDataChange) onDataChange();
    } catch (err) {
      // Rollback the optimistic override on failure.
      setExclusiveGroupCodesOverride(null);
      showToast(formatErrorMessage(err, t).primary || t('common.error'), 'error');
    }
  };

  // Drop the optimistic override once the parent supplies the new value.
  useEffect(() => {
    if (exclusiveGroupCodesOverride === null) return;
    if (!!category?.exclusive_group_codes === exclusiveGroupCodesOverride) {
      setExclusiveGroupCodesOverride(null);
    }
  }, [category?.exclusive_group_codes, exclusiveGroupCodesOverride]);

  // ─── Engine: toggle a mark in/out of priorities list ───
  const handleMarkPriorityToggle = async (markId) => {
    const idx = activeMarkPriorityList.findIndex(e => e.id === markId);
    const updated = idx >= 0
      ? activeMarkPriorityList.filter(e => e.id !== markId)
      : [...activeMarkPriorityList, { id: markId, behaviour: _markBehaviourFromDef(markId) }];
    await handleEngineSettingChange('mark_priorities', updated);
  };

  // v1.0-pre #23: change a mark's per-category cluster behaviour.
  const handleMarkBehaviourChange = async (markId, behaviour) => {
    const updated = activeMarkPriorityList.map(e =>
      e.id === markId ? { ...e, behaviour } : e
    );
    await handleEngineSettingChange('mark_priorities', updated);
  };

  // ─── Engine: reorder mark priorities (button-based, ↑↓) ───
  const handleMarkPriorityReorder = async (fromIdx, toIdx) => {
    const updated = [...activeMarkPriorityList];
    const [moved] = updated.splice(fromIdx, 1);
    updated.splice(toIdx, 0, moved);
    await handleEngineSettingChange('mark_priorities', updated);
  };

  // ─── Engine: drag-and-drop reorder for marks ───
  const handleMarkDragStart = (markId) => setDragMarkId(markId);
  const handleMarkDragOver = (e, markId) => {
    e.preventDefault();
    if (dragMarkId && dragMarkId !== markId) setDragOverMarkId(markId);
  };
  const handleMarkDragLeave = () => setDragOverMarkId(null);
  const handleMarkDrop = async (toMarkId) => {
    if (!dragMarkId || dragMarkId === toMarkId) {
      setDragMarkId(null);
      setDragOverMarkId(null);
      return;
    }
    const fromIdx = activeMarkPriorities.indexOf(dragMarkId);
    const toIdx = activeMarkPriorities.indexOf(toMarkId);
    setDragMarkId(null);
    setDragOverMarkId(null);
    if (fromIdx === -1 || toIdx === -1) return;
    await handleMarkPriorityReorder(fromIdx, toIdx);
  };

  // ─── Unit CRUD ───
  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    try {
      // v0.74: capacity is required at the schema layer (NOT NULL).
      // When the category's has_capacity toggle is off OR the form
      // field is empty, default to 1. The engine ignores caps when
      // the toggle is off, so this is a placeholder value the
      // organiser can adjust later. Gender_restriction stays gated
      // on category.has_gender_restriction (still in DB; deprecated).
      await allocationUnits.create(eventId, category.id, {
        name: form.name.trim(),
        description: form.description.trim() || null,
        capacity: form.capacity ? parseInt(form.capacity) : 1,
        gender_restriction: category.has_gender_restriction && form.gender_restriction ? form.gender_restriction : null,
      });
      setForm({ name: '', description: '', capacity: '', gender_restriction: '' });
      setShowCreate(false);
      await loadAll();
      if (onDataChange) onDataChange();
    } catch (err) { setError(err); }
  };

  const handleUpdateUnit = async (e) => {
    e.preventDefault();
    if (!editingUnit) return;
    try {
      await allocationUnits.update(eventId, category.id, editingUnit.id, {
        name: editingUnit.name,
        description: editingUnit.description || null,
        // v0.74: capacity required-everywhere. Fall back to 1 if cleared.
        capacity: editingUnit.capacity ? parseInt(editingUnit.capacity) : 1,
        gender_restriction: editingUnit.gender_restriction || null,
      });
      setEditingUnit(null);
      await loadAll();
      if (onDataChange) onDataChange();
      showToast(`${itemLabel} updated`);
    } catch (err) { setError(err); }
  };

  // v1.0.0q: inline-rename handlers. Same shape as the group-type
  // title rename in OrganiseDashboard but scoped to one field.
  const startInlineRenameUnit = (unit) => {
    setEditingUnitRenameId(unit.id);
    setUnitRenameDraft(unit.name || '');
  };
  const commitInlineRenameUnit = async (unitId) => {
    const trimmed = (unitRenameDraft || '').trim();
    const existing = units.find(u => u.id === unitId);
    if (!trimmed || (existing && trimmed === existing.name)) {
      setEditingUnitRenameId(null);
      setUnitRenameDraft('');
      return;
    }
    try {
      await allocationUnits.update(eventId, category.id, unitId, {
        name: trimmed,
        description: existing?.description || null,
        capacity: existing?.capacity ? parseInt(existing.capacity) : 1,
        gender_restriction: existing?.gender_restriction || null,
      });
      await loadAll();
      if (onDataChange) onDataChange();
    } catch (err) {
      setError(err);
    }
    setEditingUnitRenameId(null);
    setUnitRenameDraft('');
  };
  const cancelInlineRenameUnit = () => {
    setEditingUnitRenameId(null);
    setUnitRenameDraft('');
  };

  const handleDeleteUnit = async (unitId) => {
    const ok = await confirm({
      title: `Delete ${itemLabel}?`,
      message: `This will permanently remove this ${itemLabel.toLowerCase()} and all its participant assignments. This cannot be undone.`,
      confirmLabel: 'Delete',
      danger: true,
    });
    if (!ok) return;
    try {
      await allocationUnits.delete(eventId, category.id, unitId);
      await loadAll();
      if (onDataChange) onDataChange();
    } catch (err) { setError(err); }
  };

  // ─── Computed ───
  // v50c-3c-2d: include BOTH pending and confirmed participants. Organisers
  // routinely allocate people before email confirmation has completed, and
  // previously an unassigned pending participant would vanish from the UI
  // entirely (not in units, not in unassigned pool). Only truly cancelled
  // registrations are excluded.
  const activeParticipants = participantList.filter(p => p.registration_status !== 'cancelled');
  const isOverlapping = category.rule_type === 'overlapping';
  const allAssignedIds = new Set();
  Object.values(allMembers).forEach(m => m.forEach(x => allAssignedIds.add(x.participant_id)));
  const unassigned = activeParticipants.filter(p => !allAssignedIds.has(String(p.id)));

  // v0.72: live-recomputed mark cluster splits for the hint strip.
  // useMemo keyed on the four data sources that affect the result —
  // any drag/drop/edit that changes allMembers triggers a recompute.
  // Pure function; cheap (O(N) over assignments + placed members);
  // safe to recompute on every render-cycle.
  // v1.0.0o: pass the active mark_priorities for this category so the
  // hint strip only reports splits on marks the organiser actually
  // asked the engine to keep together. Two filter layers:
  //   1. Mark must be in this category's mark_priorities.
  //   2. Effective cluster_behaviour must be 'together' — a mark
  //      configured as 'split' is *expected* to spread across units,
  //      so reporting its spread would be wrong, not informative.
  // activeMarkPriorityList (built around line 485) carries both id
  // and effective behaviour, so this slice is cheap.
  const activeMarkPriorityIds = useMemo(
    () => activeMarkPriorityList
      .filter(e => e.behaviour === 'together')
      .map(e => e.id),
    [activeMarkPriorityList]
  );
  const markSplits = useMemo(
    () => computeMarkSplits({
      allMembers, units, markAssignments, markDefs,
      activeMarkPriorityIds,
    }),
    [allMembers, units, markAssignments, markDefs, activeMarkPriorityIds]
  );

  const leftPanelPeople = isOverlapping ? activeParticipants : unassigned;
  const leftPanelLabel = isOverlapping ? t('organise.all_participants') : t('organise.unassigned_panel');
  const leftPanelCount = isOverlapping ? activeParticipants.length : unassigned.length;

  // v0.73b Q1/Q2/Q3: pending vs unassigned-confirmed split.
  // - Q1: each pending participant gets a "Wartet" pill (rendered inline).
  // - Q2: the count banner splits "N nicht zugewiesen (M wartet)" when
  //   pending count > 0; falls back to single-count phrasing otherwise.
  // - Q3: pending sort to the bottom of the unassigned list so the
  //   organiser's actionable items (confirmed-but-unassigned) float up.
  // The split uses registration_status === 'pending' as the marker.
  // Cancelled is already excluded by activeParticipants. The split
  // only runs in the non-overlapping (exclusive) view because pending
  // status doesn't carry through to overlapping categories the same way.
  const pendingCount = isOverlapping
    ? 0
    : unassigned.filter(p => p.registration_status === 'pending').length;
  const unassignedConfirmedCount = leftPanelCount - pendingCount;

  const filteredLeftPanel = leftPanelPeople.filter(p => {
    const q = search.toLowerCase();
    const nameMatch = !q || `${p.first_name} ${p.last_name}`.toLowerCase().includes(q) || (p.group_code && p.group_code.toLowerCase().includes(q));
    const genderMatch = !genderFilter || p.gender === genderFilter;
    return nameMatch && genderMatch;
  });

  // v0.73b Q3: in non-overlapping categories, pending participants
  // sort to the bottom so confirmed-but-unassigned (actionable) ones
  // float to the top. Stable within each bucket — within pending or
  // within confirmed, the original order is preserved. For
  // overlapping categories the original order stands; pending status
  // doesn't change drag-drop priority there.
  const sortedLeftPanel = isOverlapping
    ? filteredLeftPanel
    : [...filteredLeftPanel].sort((a, b) => {
        const aPending = a.registration_status === 'pending' ? 1 : 0;
        const bPending = b.registration_status === 'pending' ? 1 : 0;
        return aPending - bPending;
      });

  const totalOccupied = units.reduce((s, u) => s + u.occupant_count, 0);
  const getNoteCount = (type, id) => noteCounts?.[`${type}:${id}`] || 0;

  // v0.70d-2e-3 (AB3 Q2 composed transition): derive "ready to
  // confirm" state for the top progress row. Triggers when the
  // category is fully allocated but not yet confirmed. The
  // additional guards make sure we don't fire spuriously:
  //   - activeParticipants.length > 0: don't celebrate empty
  //     categories (a category with no participants would
  //     trivially have unassigned.length === 0 too)
  //   - !isOverview: read-only overview mode shouldn't show
  //     a confirm CTA
  //   - !isOverlapping: overlapping categories don't have an
  //     "all assigned" goalpost — every participant is
  //     "assigned" to all units by definition, so the pill at
  //     line 1090 doesn't fire either; we mirror that gate
  // Mirrors S3 (gate card) implementation in SetupHub. Same
  // .gate-flash CSS class is reused — the moment vocabulary is
  // identical (something just became ready, here's the next
  // step). Direction-aware: flash fires on false→true ONLY,
  // never on regression (e.g. organiser drags someone back to
  // the unassigned pool, breaking readiness; or admin
  // un-confirms via the banner below).
  const isReadyToConfirm = (
    !isOverview
    && !isOverlapping
    && !category?.confirmed
    && activeParticipants.length > 0
    && unassigned.length === 0
  );
  const prevReadyRef = useRef(isReadyToConfirm);
  const [readyFlashing, setReadyFlashing] = useState(false);
  useEffect(() => {
    const prev = prevReadyRef.current;
    prevReadyRef.current = isReadyToConfirm;
    if (prev === false && isReadyToConfirm === true && !prefersReducedMotion) {
      setReadyFlashing(true);
      const timer = setTimeout(() => setReadyFlashing(false), 400);
      return () => clearTimeout(timer);
    }
  }, [isReadyToConfirm, prefersReducedMotion]);

  // v0.70d-2a (R8a/R8b/R8c): capacity color gradient re-mapped.
  // Below 80% capacity is ample — no signal needed, so neutral tint
  // (previously bright green, which screams "success!" when it's
  // really just "not full yet"). At 80%+ the organiser is likely to
  // revisit this unit — pending. At exactly capacity (100%), red
  // stays as a "no more room" alarm. Over-capacity stays burgundy
  // for clarity that an override has happened.
  const capColor = (occ, cap) => {
    if (!cap) return 'bg-neutral-tint text-muted';
    const pct = occ / cap;
    // v0.54: pct > 1 means organiser has manually overbooked. Burgundy
    // signal to make the exceeded state immediately obvious at a glance.
    if (pct > 1)    return 'bg-[rgba(128,0,32,0.12)] text-[var(--alert-burgundy)]';
    if (pct >= 1)   return 'bg-red-100 text-red-600';    // exactly at cap
    if (pct >= 0.8) return 'bg-pending-tint text-pending';
    return 'bg-neutral-tint text-muted';
  };

  const isDropValid = (_unitId) => {
    if (!dragParticipant) return true;
    // v0.54: capacity is a SOFT constraint on manual drops — the organiser
    // may knowingly overbook a unit. The card surfaces a burgundy signal
    // once the drop lands. Gender restriction (if any) is still HARD and
    // enforced by the backend; a rejected drop surfaces as an error toast.
    return true;
  };

  // ─── Selection ───
  const toggleSelect = (pid) => {
    const next = new Set(selectedPeople);
    if (next.has(pid)) next.delete(pid); else next.add(pid);
    setSelectedPeople(next);
    setAssignDropdown(false);
  };

  // ─── Assignment ───
  const findName = (pid) => {
    const p = activeParticipants.find(p => String(p.id) === String(pid));
    if (p) return `${p.first_name} ${p.last_name}`;
    for (const members of Object.values(allMembers)) {
      const m = members.find(m => m.participant_id === pid);
      if (m) return m.participant_name;
    }
    return 'Participant';
  };

  const findParticipant = (pid) => activeParticipants.find(p => String(p.id) === String(pid));

  const handleUnassign = async (unitId, participantId) => {
    try {
      // v1.0.0e: unassign now returns 200 with `{warning}`. When the
      // backend computed a soft warning (manual move broke an engine-
      // honoured constraint), surface it as a gold toast instead of
      // the standard "removed" success toast. Single visible toast at
      // a time — useToast collapses to the latest call.
      const res = await allocApi.unassign(eventId, unitId, participantId);
      const unitName = units.find(u => String(u.id) === String(unitId))?.name || itemLabel;
      const w = res?.warning;
      if (w?.key) {
        showToast(t(w.key, w.params || {}), 'warning');
      } else {
        showToast(
          t('organise.toast.removed', {
            name: dragParticipant?.name || '',
            unit: unitName,
          })
        );
      }
      await loadAll();
      if (onDataChange) onDataChange();
    } catch (err) { showToast(err, 'error'); }
  };

  const handleBulkAssign = async (unitId) => {
    setAssignDropdown(false);
    const ids = [...selectedPeople];
    let ok = 0, fail = 0;
    let firstErr = null;
    for (const pid of ids) {
      try { await allocApi.assign(eventId, pid, unitId); ok++; }
      catch (err) { fail++; if (!firstErr) firstErr = err; }
    }
    setSelectedPeople(new Set());
    await loadAll();
    if (onDataChange) onDataChange();
    const uName = units.find(u => String(u.id) === String(unitId))?.name || itemLabel;
    if (fail > 0) {
      // v0.73e Finding 3: surface the actual reason instead of the
      // pre-fix hardcoded "could not be placed" generic. Single
      // failure → the specific error string. Mixed failure → the
      // aggregate key with count + reason.
      const reason = formatErrorMessage(firstErr, t).primary;
      if (ok === 0 && fail === 1) {
        showToast(reason, 'error');
      } else {
        showToast(t('organise.toast.bulk_partial', { ok, fail, unit: uName, reason }), 'error');
      }
    }
    else showToast(t('organise.toast.bulk_assigned', { count: ok, unit: uName }), 'success');
  };

  const handleUnitCardClick = async (unit) => {
    if (selectedPeople.size === 0) return;
    const n = selectedPeople.size;
    const ok = await confirm({
      title: `Assign ${n} participant${n !== 1 ? 's' : ''} to ${unit.name}?`,
      message: `This will place the selected participant${n !== 1 ? 's' : ''} into "${unit.name}".`,
      confirmLabel: 'Assign',
    });
    if (!ok) return;
    await handleBulkAssign(unit.id);
  };

  const handleBulkUnassign = async () => {
    const ids = [...selectedPeople];
    let ok = 0, fail = 0;
    for (const pid of ids) {
      const theirUnits = units.filter(u => (allMembers[String(u.id)] || []).some(m => m.participant_id === pid));
      for (const unit of theirUnits) {
        try { await allocApi.unassign(eventId, unit.id, pid); ok++; }
        catch { fail++; }
      }
    }
    setSelectedPeople(new Set());
    await loadAll();
    if (onDataChange) onDataChange();
    if (ok === 0) showToast(t('organise.toast.none_to_remove'));
    else if (fail > 0) showToast(`${ok} removed, ${fail} failed`, 'error');
    else showToast(t('organise.toast.unassigned', { n: ids.length }), 'success');
  };

  // ─── Drag & Drop ───
  const handleDrop = async (targetUnitId) => {
    setDragOverUnit(null);
    if (!dragParticipant || targetUnitId === dragSource) { setDragParticipant(null); setDragSource(null); return; }

    // v0.55.1: if the drop would take the target unit over capacity, ask
    // the organiser to confirm first. Gender restriction (hard) is still
    // enforced by the backend and surfaces as an error toast in the catch
    // below. For bulk drops we check against the additional count.
    const targetUnit = units.find(u => String(u.id) === String(targetUnitId));
    if (category.has_capacity && targetUnit && targetUnit.capacity) {
      const adding = dragParticipant.bulk?.length > 1 ? dragParticipant.bulk.length : 1;
      // How many of the dropped participants are NOT currently in the target
      // unit? (Bulk drops may include people already here — they don't add.)
      const currentMembersSet = new Set(
        (allMembers[String(targetUnitId)] || []).map(m => String(m.participant_id))
      );
      const ids = dragParticipant.bulk?.length > 1
        ? dragParticipant.bulk.map(String)
        : [String(dragParticipant.id)];
      const newArrivals = ids.filter(pid => !currentMembersSet.has(pid)).length;
      const projected = targetUnit.occupant_count + newArrivals;
      if (projected > targetUnit.capacity) {
        const displayName = dragParticipant.bulk?.length > 1
          ? `${adding} ${t('nav.people').toLowerCase()}`
          : findName(dragParticipant.id);
        const ok = await confirm({
          title: t('organise.overbook_confirm.title', { unit: targetUnit.name }),
          message: t('organise.overbook_confirm.message', {
            name: displayName,
            unit: targetUnit.name,
            projected,
            capacity: targetUnit.capacity,
          }),
          confirmLabel: t('organise.overbook_confirm.button'),
          danger: true,
        });
        if (!ok) {
          setDragParticipant(null);
          setDragSource(null);
          return;
        }
      }
    }

    try {
      if (dragParticipant.bulk && dragParticipant.bulk.length > 1) {
        let ok = 0, fail = 0;
        let firstErr = null;
        for (const pid of dragParticipant.bulk) {
          try {
            if (isOverlapping) {
              await allocApi.assign(eventId, pid, targetUnitId);
            } else {
              const currentUnit = units.find(u => (allMembers[String(u.id)] || []).some(m => m.participant_id === pid));
              if (currentUnit) await allocApi.move(eventId, pid, targetUnitId);
              else await allocApi.assign(eventId, pid, targetUnitId);
            }
            ok++;
          } catch (err) { fail++; if (!firstErr) firstErr = err; }
        }
        setSelectedPeople(new Set());
        const toName = units.find(u => String(u.id) === String(targetUnitId))?.name;
        if (fail > 0) {
          // v0.73e Finding 3: see handleBulkAssign for rationale.
          const reason = formatErrorMessage(firstErr, t).primary;
          if (ok === 0 && fail === 1) {
            showToast(reason, 'error');
          } else {
            showToast(t('organise.toast.bulk_partial', { ok, fail, unit: toName, reason }), 'error');
          }
        }
        else showToast(t('organise.toast.bulk_assigned', { count: ok, unit: toName }), 'success');
      } else {
        const pName = findName(dragParticipant.id);
        const fromName = dragSource && dragSource !== 'unassigned' ? units.find(u => String(u.id) === String(dragSource))?.name : null;
        const toName = units.find(u => String(u.id) === String(targetUnitId))?.name;
        // v1.0.0e: capture the call's warning. Single toast at a time:
        // when a warning is present (manual move broke an engine-
        // honoured cluster), it overrides the "Alice: Room A → Room B"
        // success toast — the warning carries enough context that
        // separately announcing the move would be redundant noise.
        let res;
        if (isOverlapping) {
          if (dragSource && dragSource !== 'unassigned') await allocApi.unassign(eventId, dragSource, dragParticipant.id);
          res = await allocApi.assign(eventId, dragParticipant.id, targetUnitId);
        } else {
          if (dragSource && dragSource !== 'unassigned') res = await allocApi.move(eventId, dragParticipant.id, targetUnitId);
          else res = await allocApi.assign(eventId, dragParticipant.id, targetUnitId);
        }
        const w = res?.warning;
        if (w?.key) {
          showToast(t(w.key, w.params || {}), 'warning');
        } else {
          showToast(fromName ? `${pName}: ${fromName} → ${toName}` : `${pName} → ${toName}`, 'success');
        }
      }
      await loadAll();
      if (onDataChange) onDataChange();
    } catch (err) { showToast(err, 'error'); }
    finally { setDragParticipant(null); setDragSource(null); }
  };

  const handleDropUnassigned = async () => {
    setDragOverUnit(null);
    if (!dragParticipant || !dragSource || dragSource === 'unassigned') { setDragParticipant(null); setDragSource(null); return; }
    try {
      if (dragParticipant.bulk && dragParticipant.bulk.length > 1) {
        for (const pid of dragParticipant.bulk) {
          const theirUnits = units.filter(u => (allMembers[String(u.id)] || []).some(m => m.participant_id === pid));
          for (const unit of theirUnits) {
            try { await allocApi.unassign(eventId, unit.id, pid); } catch {}
          }
        }
        setSelectedPeople(new Set());
        showToast(t('organise.toast.unassigned', { n: dragParticipant.bulk.length }), 'success');
      } else {
        const pName = findName(dragParticipant.id);
        const fromName = units.find(u => String(u.id) === String(dragSource))?.name;
        // v1.0.0e: same single-toast precedence as handleDrop. When the
        // unassign breaks an engine-honoured cluster, the gold warning
        // toast supersedes the plain "X removed from Y" success line.
        const res = await allocApi.unassign(eventId, dragSource, dragParticipant.id);
        const w = res?.warning;
        if (w?.key) {
          showToast(t(w.key, w.params || {}), 'warning');
        } else {
          showToast(`${pName} removed from ${fromName || itemLabel}`);
        }
      }
      await loadAll();
      if (onDataChange) onDataChange();
    } catch (err) { showToast(err, 'error'); }
    finally { setDragParticipant(null); setDragSource(null); }
  };

  if (loading) return <p className="text-gray-400 text-sm">{t('common.loading')}</p>;

  const catNotesCount = getNoteCount('category', category.id);

  return (
    <div className="relative">
      {/* v0.70d-1 R2 + R8a: ToastHost replaces the inline render block.
          Same visual position (top-right with safe-area), semantic
          tokens for colours (io-accent / alert-burgundy / card),
          and identical 3-second auto-dismiss behaviour. The raw
          '#1E7A34' green from pre-v0.70d is gone. */}
      <ToastHost />

      <TranslatedError err={error} />

      {/* v0.70d-1 R1: in-place review surface. When a proposal is
          active, the review takes over the board body. The top-level
          wrapper, ToastHost, and error banner stay visible above.
          Everything below (stats bar, engine row, unit cards, etc.)
          is skipped via early return. Discard/Commit both clear
          `proposal`, restoring the normal board render. */}
      {proposal && (
        <>
          <ReviewSurface
            proposal={proposal}
            existingUnits={units}
            allMembers={allMembers}
            participantList={participantList}
            committing={committing}
            onCommit={handleCommit}
            onDiscard={() => setProposal(null)}
          />
          <ConfirmOverlay />
        </>
      )}
      {!proposal && (<>

      {/* Stats bar + Engine controls */}
      <div
        className="card-surface-solid rounded-2xl p-3 mb-4"
        style={{ border: '1px solid var(--card-border)' }}
      >

        {/* v0.50p: Confirmed banner — only when the category is confirmed.
            Shows state and offers Unconfirm so the reversal lives with
            the other category controls rather than on the dashboard card.
            Steel-blue tint (informational, not destructive).
            v0.70d-2e-3 (AB4): post-confirmation direction hint. The
            audit's finding was that after confirming, the surface
            "sits there" with no nudge toward the next allocation
            category or the next workflow phase. We compute next from
            allCategories (passed by OrganiseDashboard); if there's
            an unconfirmed category remaining, render a "Next: {name}"
            link that calls onSelectCategory; otherwise render an
            "All confirmed · Check-in is ready →" link to the
            check-in route. Optional chaining on the props means
            OverviewPage's read-only render (which doesn't pass them)
            simply skips the hint — graceful no-op, no break. */}
        {category?.confirmed && (() => {
          // Compute "next" target. If allCategories isn't available
          // (overview/read-only mounts), the hint is suppressed entirely.
          const nextCat = allCategories?.find(c => !c.confirmed && c.id !== category.id);
          const allDone = allCategories && allCategories.length > 0 && !nextCat;
          return (
          <div
            className="flex items-center justify-between gap-3 rounded-card px-3 py-2 mb-3 flex-wrap"
            style={{
              background: 'rgba(70,130,180,0.06)',
              border: '1px solid rgba(70,130,180,0.22)',
            }}
          >
            <div className="flex items-center gap-2 min-w-0">
              <span style={{ color: 'var(--io-accent)' }} aria-hidden="true">✓</span>
              <span className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>
                {t('alloc.status.confirmed')}
              </span>
              <span className="text-[11px]" style={{ color: 'var(--text-subtle)' }}>
                {t('alloc.confirmed.hint')}
              </span>
            </div>
            <div className="flex items-center gap-3 flex-wrap shrink-0">
              {/* AB4 directional hint */}
              {nextCat && onSelectCategory && (
                <button
                  type="button"
                  onClick={() => onSelectCategory(nextCat.id)}
                  className="text-[11px] font-semibold hover:underline whitespace-nowrap"
                  style={{ color: 'var(--io-accent)' }}
                >
                  {t('alloc.next_group_type', { name: nextCat.name })}
                </button>
              )}
              {allDone && (
                <button
                  type="button"
                  onClick={() => navigate(`/admin/events/${eventId}/checkin`)}
                  className="text-[11px] font-semibold hover:underline whitespace-nowrap"
                  style={{ color: 'var(--io-accent)' }}
                >
                  {t('alloc.all_confirmed_hint')}
                </button>
              )}
              {isAdmin && (
                <button
                  type="button"
                  onClick={handleUnconfirmCategory}
                  disabled={unconfirming}
                  className="text-[11px] font-semibold px-3 py-1 rounded-md border hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-50 whitespace-nowrap"
                  style={{ borderColor: 'var(--card-border)', color: 'var(--text-muted)' }}
                >
                  {unconfirming
                    ? (t('common.loading'))
                    : (t('alloc.cta.unconfirm'))}
                </button>
              )}
            </div>
            {unconfirmError && (
              <p className="w-full text-xs" style={{ color: 'var(--alert-burgundy)' }}>{formatErrorMessage(unconfirmError, t).primary}</p>
            )}
          </div>
          );
        })()}

        {/* v0.72: System hints strip — mark cluster splits + unallocated
            count. Mounted only when the category is unconfirmed; on
            confirm, the confirmed banner above replaces this surface
            entirely (decision: hints disappear once the organiser has
            committed to the allocation). The component itself returns
            null when both signals are zero, so it never renders an
            empty box. */}
        {!category?.confirmed && (
          <CategoryHintsStrip
            markSplits={markSplits}
            unallocatedCount={unassigned.length}
          />
        )}

        {/* ── Engine row: split button + overflow menu ── */}
        {isAdmin && !isOverview && (
          <div className="flex items-center gap-2 mb-3 pb-3" style={{ borderBottom: '1px solid var(--card-border)' }}>

            {/* Split button: [✦ Auto-allocate | ⚙] */}
            <div className="flex rounded-card shadow-sm relative" style={{ border: '1px solid #FFD700' }}>
              {/* Left half — opens mode picker */}
              <button
                disabled={suggesting || units.length === 0}
                onClick={() => setShowModePicker(p => !p)}
                className="bg-gold text-deep-navy font-bold text-sm px-4 py-2 hover:bg-gold/80 disabled:opacity-40 transition-colors flex items-center gap-2"
                title={units.length === 0 ? t('engine.no_units_hint', { item: itemLabel }) : t('engine.run_from_board', { item: itemLabel })}>
                {suggesting ? <span className="animate-spin inline-block">⟳</span> : <span>✦</span>}
                {suggesting ? t('engine.suggesting') : t('engine.auto_allocate')}
              </button>
              {/* Divider */}
              <span className="w-px shrink-0" style={{ background: 'rgba(15,30,46,0.2)' }} />
              {/* Right half — engine settings */}
              <div className="relative" ref={engineSettingsRef} onMouseDown={e => e.stopPropagation()}>
                <button
                  onClick={() => { setShowEngineSettings(p => !p); setShowModePicker(false); }}
                  className={`bg-gold text-deep-navy px-3 py-2 hover:bg-gold/80 transition-colors text-sm ${showEngineSettings ? 'bg-gold/70' : ''}`}
                  title={t('engine.settings_icon')}>
                  ⚙
                </button>
                {showEngineSettings && (
                  <div
                    className="card-surface-solid absolute top-full left-0 mt-1 rounded-card p-4 z-30 w-72"
                    style={{ border: '1px solid var(--card-border)', boxShadow: '0 12px 32px rgba(0,0,0,0.25)' }}>
                    <p className="text-[10px] font-semibold uppercase tracking-caps mb-3" style={{ color: 'var(--text-subtle)' }}>
                      {t('engine.settings.title')}
                    </p>
                    <div className="space-y-2.5">
                      <label className="flex items-start gap-2 cursor-pointer">
                        <input type="checkbox"
                          checked={engineSettings.use_group_codes ?? true}
                          onChange={e => handleEngineSettingChange('use_group_codes', e.target.checked)}
                          className="h-3.5 w-3.5 rounded mt-0.5 accent-steel-blue dark:accent-gold" />
                        <div>
                          <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
                            {t('engine.settings.use_group_codes')}
                          </span>
                          <p className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>
                            {t('engine.settings.use_group_codes.hint')}
                          </p>
                        </div>
                      </label>
                      <label className="flex items-start gap-2 cursor-pointer">
                        <input type="checkbox"
                          checked={engineSettings.group_remaining_by_gender ?? true}
                          onChange={e => handleEngineSettingChange('group_remaining_by_gender', e.target.checked)}
                          className="h-3.5 w-3.5 rounded mt-0.5 accent-steel-blue dark:accent-gold" />
                        <div>
                          <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
                            {t('engine.settings.group_by_gender')}
                          </span>
                          <p className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>
                            {t('engine.settings.group_by_gender.hint')}
                          </p>
                        </div>
                      </label>
                      <label className="flex items-start gap-2 cursor-pointer">
                        <input type="checkbox"
                          checked={engineSettings.split_oversized_groups ?? true}
                          onChange={e => handleEngineSettingChange('split_oversized_groups', e.target.checked)}
                          className="h-3.5 w-3.5 rounded mt-0.5 accent-steel-blue dark:accent-gold" />
                        <div>
                          <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
                            {t('engine.settings.split_groups')}
                          </span>
                          <p className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>
                            {t('engine.settings.split_groups.hint')}
                          </p>
                        </div>
                      </label>
                      {/* v0.73b: include_pending_in_allocation toggle.
                          Default ON; ?? true matches the convention of
                          the other toggles so categories with no engine
                          settings block read as if the toggle is on. */}
                      <label className="flex items-start gap-2 cursor-pointer">
                        <input type="checkbox"
                          checked={engineSettings.include_pending_in_allocation ?? true}
                          onChange={e => handleEngineSettingChange('include_pending_in_allocation', e.target.checked)}
                          className="h-3.5 w-3.5 rounded mt-0.5 accent-steel-blue dark:accent-gold" />
                        <div>
                          <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
                            {t('engine.settings.include_pending')}
                          </span>
                          <p className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>
                            {t('engine.settings.include_pending.hint')}
                          </p>
                        </div>
                      </label>
                      {/* v1.0.0e: equalise_after_allocation toggle. After
                          all rule-based passes, the engine moves whole
                          clusters between units to make occupancies more
                          even (proportional to capacity). Default ON;
                          ?? true so categories with no engine settings
                          block read as if the toggle is on. */}
                      <label className="flex items-start gap-2 cursor-pointer">
                        <input type="checkbox"
                          checked={engineSettings.equalise_after_allocation ?? true}
                          onChange={e => handleEngineSettingChange('equalise_after_allocation', e.target.checked)}
                          className="h-3.5 w-3.5 rounded mt-0.5 accent-steel-blue dark:accent-gold" />
                        <div>
                          <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
                            {t('engine.settings.equalise')}
                          </span>
                          <p className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>
                            {t('engine.settings.equalise.hint')}
                          </p>
                        </div>
                      </label>
                      {/* v1.0-pre #24: exclusive_group_codes — moved here
                          from the group-type editor. Reads/writes the
                          top-level category field directly (not inside
                          settings.engine), via its own handler. */}
                      <label className="flex items-start gap-2 cursor-pointer">
                        <input type="checkbox"
                          checked={exclusiveGroupCodesValue}
                          onChange={e => handleExclusiveGroupCodesToggle(e.target.checked)}
                          className="h-3.5 w-3.5 rounded mt-0.5 accent-steel-blue dark:accent-gold" />
                        <div>
                          <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
                            {t('organise.exclusive_group_codes')}
                          </span>
                          <p className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>
                            {t('organise.exclusive_group_codes.hint')}
                          </p>
                        </div>
                      </label>
                    </div>
                    {/* Mark priorities */}
                    <div className="pt-3 mt-3" style={{ borderTop: '1px solid var(--card-border)' }}>
                      <p className="text-[10px] font-semibold uppercase tracking-caps mb-1" style={{ color: 'var(--text-subtle)' }}>
                        {t('engine.settings.mark_priorities')}
                      </p>
                      <p className="text-[10px] mb-2" style={{ color: 'var(--text-subtle)' }}>
                        {t('engine.settings.mark_priorities.hint')}
                      </p>
                      {markDefs.length === 0 ? (
                        <p className="text-[10px] italic" style={{ color: 'var(--text-subtle)' }}>
                          {t('engine.settings.no_marks')}
                        </p>
                      ) : (
                        <div className="space-y-1">
                          {activeMarkPriorities.map((mid, idx) => {
                            const def = markDefs.find(d => String(d.id) === mid);
                            if (!def) return null;
                            const isDragOver = dragOverMarkId === mid && dragMarkId !== mid;
                            const isDragging = dragMarkId === mid;
                            // v1.0-pre #23: per-mark cluster behaviour. Reads
                            // from the parallel object list above; falls back
                            // to the global mark.cluster_behaviour for entries
                            // that haven't been touched since the model change.
                            const entry = activeMarkPriorityList.find(e => e.id === mid);
                            const behaviour = entry?.behaviour || 'none';
                            return (
                              <div key={mid} draggable
                                onDragStart={() => handleMarkDragStart(mid)}
                                onDragOver={(e) => handleMarkDragOver(e, mid)}
                                onDragLeave={handleMarkDragLeave}
                                onDrop={() => handleMarkDrop(mid)}
                                onDragEnd={() => { setDragMarkId(null); setDragOverMarkId(null); }}
                                className="flex items-center gap-2 rounded-card px-2 py-1.5 cursor-move transition-all"
                                style={isDragOver
                                  ? { background: 'rgba(70,130,180,0.20)', boxShadow: 'inset 0 0 0 2px var(--io-accent)' }
                                  : isDragging
                                    ? { background: 'rgba(70,130,180,0.05)', opacity: 0.4 }
                                    : { background: 'rgba(70,130,180,0.05)' }}>
                                <span className="text-[10px] select-none" style={{ color: 'var(--text-subtle)', opacity: 0.5 }}>⠿</span>
                                <span className="text-[10px] font-bold w-4 text-center" style={{ color: 'var(--io-accent)' }}>{idx + 1}</span>
                                <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: def.colour }} />
                                <span className="text-xs font-medium flex-1 truncate" style={{ color: 'var(--text-primary)' }}>{def.name}</span>
                                {/* v1.0-pre #23: per-category behaviour select.
                                    Stops propagation so changing the dropdown
                                    doesn't accidentally start a drag. */}
                                <select
                                  draggable={false}
                                  value={behaviour}
                                  onClick={(e) => e.stopPropagation()}
                                  onChange={(e) => { e.stopPropagation(); handleMarkBehaviourChange(mid, e.target.value); }}
                                  className="text-[10px] px-1.5 py-0.5 rounded"
                                  style={{
                                    background: 'var(--card-bg-solid)',
                                    border: '1px solid var(--card-border)',
                                    color: 'var(--text-muted)',
                                  }}
                                  title={t('engine.settings.mark_behaviour.hint')}>
                                  <option value="none">{t('marks.cluster_behaviour.none')}</option>
                                  <option value="together">{t('marks.cluster_behaviour.together')}</option>
                                  <option value="split">{t('marks.cluster_behaviour.split')}</option>
                                </select>
                                <div className="flex gap-0.5">
                                  {idx > 0 && <button draggable={false} onClick={(e) => { e.stopPropagation(); handleMarkPriorityReorder(idx, idx - 1); }} className="text-[10px] px-1 hover:underline" style={{ color: 'var(--text-subtle)' }}>↑</button>}
                                  {idx < activeMarkPriorities.length - 1 && <button draggable={false} onClick={(e) => { e.stopPropagation(); handleMarkPriorityReorder(idx, idx + 1); }} className="text-[10px] px-1 hover:underline" style={{ color: 'var(--text-subtle)' }}>↓</button>}
                                </div>
                                <button draggable={false} onClick={(e) => { e.stopPropagation(); handleMarkPriorityToggle(mid); }} className="text-[10px] px-1 hover:underline" style={{ color: 'var(--alert-burgundy)' }}>✕</button>
                              </div>
                            );
                          })}
                          {markDefs.filter(d => !activeMarkPriorities.includes(String(d.id))).map(def => (
                            <button key={def.id} onClick={() => handleMarkPriorityToggle(String(def.id))}
                              className="flex items-center gap-2 w-full rounded-card px-2 py-1.5 hover:bg-black/5 dark:hover:bg-white/10 transition-colors text-left">
                              <span className="w-4" />
                              <span className="w-3 h-3 rounded-full shrink-0 opacity-40" style={{ backgroundColor: def.colour }} />
                              <span className="text-xs flex-1 truncate" style={{ color: 'var(--text-subtle)' }}>{def.name}</span>
                              <span className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>+ {t('common.add')}</span>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Mode picker popover */}
            {showModePicker && (
              <div
                className="card-surface-solid absolute top-14 left-3 z-40 rounded-card p-3 w-64"
                style={{ border: '1px solid var(--card-border)', boxShadow: '0 12px 32px rgba(0,0,0,0.25)' }}>
                <p className="text-[10px] font-semibold uppercase tracking-caps mb-2" style={{ color: 'var(--text-subtle)' }}>
                  {t('engine.mode.title')}
                </p>
                <button onClick={() => handleSuggest('top_up')}
                  className="w-full text-left px-3 py-2.5 rounded-card transition-colors mb-1 hover:bg-black/5 dark:hover:bg-white/10">
                  <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                    {t('engine.mode.top_up')}
                  </p>
                  <p className="text-[10px] mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                    {t('engine.mode.top_up.hint')}
                  </p>
                </button>
                <button onClick={() => handleSuggest('replace')}
                  className="w-full text-left px-3 py-2.5 rounded-card transition-colors"
                  style={{ background: 'rgba(128,0,32,0.05)' }}
                  onMouseEnter={e => { e.currentTarget.style.background = 'rgba(128,0,32,0.12)'; }}
                  onMouseLeave={e => { e.currentTarget.style.background = 'rgba(128,0,32,0.05)'; }}>
                  <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                    {t('engine.mode.replace')}
                  </p>
                  <p className="text-[10px] mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                    {t('engine.mode.replace.hint')}
                  </p>
                </button>
              </div>
            )}

            {prefCount > 0 && (
              <span className="text-[10px] px-2.5 py-1 rounded-full font-medium bg-pending-tint text-pending">
                {t('engine.prefs_considered', { n: prefCount })}
              </span>
            )}

            {/* Spacer */}
            <div className="flex-1" />

            {/* ⋯ overflow menu */}
            <div className="relative" ref={overflowMenuRef}>
              <button onClick={() => setShowOverflowMenu(p => !p)}
                className="text-xs rounded-card px-2.5 py-2 transition-colors border hover:bg-black/5 dark:hover:bg-white/10"
                style={showOverflowMenu
                  ? { borderColor: 'var(--io-accent)', color: 'var(--io-accent)', background: 'rgba(70,130,180,0.05)' }
                  : { borderColor: 'var(--card-border)', color: 'var(--text-subtle)' }}>
                ⋯
              </button>
              {showOverflowMenu && (
                <div
                  className="card-surface-solid absolute top-full right-0 mt-1 rounded-card py-1 z-30 w-44"
                  style={{ border: '1px solid var(--card-border)', boxShadow: '0 12px 32px rgba(0,0,0,0.25)' }}>
                  <button onClick={() => { setNotesFor({ type: 'category', id: category.id, name: category.name }); setShowOverflowMenu(false); }}
                    className="w-full text-left px-4 py-2 text-xs flex items-center justify-between hover:bg-black/5 dark:hover:bg-white/10"
                    style={{ color: 'var(--text-muted)' }}>
                    {t('common.notes')}
                    {catNotesCount > 0 && (
                      <span className="text-[8px] px-1.5 py-0.5 rounded-full"
                        style={{ background: 'var(--io-accent)', color: 'var(--card-bg-solid)' }}>
                        {catNotesCount}
                      </span>
                    )}
                  </button>
                  {!isOverview && (
                    <button onClick={() => { window.open(`/overview/${eventId}/${category.id}`, '_blank'); setShowOverflowMenu(false); }}
                      className="w-full text-left px-4 py-2 text-xs hover:bg-black/5 dark:hover:bg-white/10"
                      style={{ color: 'var(--text-muted)' }}>
                      ↗ {t('organise.open_overview')}
                    </button>
                  )}
                  {isOverview && (
                    <button onClick={() => { window.print(); setShowOverflowMenu(false); }}
                      className="w-full text-left px-4 py-2 text-xs hover:bg-black/5 dark:hover:bg-white/10"
                      style={{ color: 'var(--text-muted)' }}>
                      {t('organise.print')}
                    </button>
                  )}
                  {!isOverview && (
                    <>
                      {/* v0.50t: inline PDF language selector. Sits above the
                          two Detailed PDF buttons because both read this
                          state. Native select kept lightweight; clicking the
                          select doesn't close the overflow menu (mousedown
                          listener only closes on outside clicks). */}
                      <div
                        className="w-full px-4 py-2 flex items-center gap-2"
                        style={{ borderTop: '1px solid var(--card-border)', borderBottom: '1px solid var(--card-border)' }}
                        onClick={e => e.stopPropagation()}
                      >
                        <label
                          htmlFor={`pdf-lang-${category.id}`}
                          className="text-[10px] font-semibold uppercase tracking-caps shrink-0"
                          style={{ color: 'var(--text-subtle)' }}
                        >
                          {t('organise.pdf_lang_label')}
                        </label>
                        <select
                          id={`pdf-lang-${category.id}`}
                          value={pdfLang}
                          onChange={e => setPdfLang(e.target.value)}
                          className="text-xs rounded border bg-transparent flex-1 px-1.5 py-0.5"
                          style={{ borderColor: 'var(--card-border)', color: 'var(--text-primary)' }}
                        >
                          {PDF_LANG_OPTIONS.map(opt => (
                            <option key={opt.code} value={opt.code}>{opt.label}</option>
                          ))}
                        </select>
                      </div>
                    </>
                  )}
                  {!isOverview && (
                    <button onClick={() => { handleDetailedPdfDownload(false); setShowOverflowMenu(false); }}
                      disabled={detailedPdfDownloading}
                      className="w-full text-left px-4 py-2 text-xs flex items-center gap-1 hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-50"
                      style={{ color: 'var(--text-muted)' }}>
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="1.8"
                        strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                      </svg>
                      {detailedPdfDownloading
                        ? (t('common.loading'))
                        : (t('organise.detailed_pdf'))}
                    </button>
                  )}
                  {!isOverview && (
                    <button onClick={() => { handleDetailedPdfDownload(true); setShowOverflowMenu(false); }}
                      disabled={detailedPdfDownloading}
                      className="w-full text-left px-4 py-2 text-xs flex items-center gap-1 hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-50"
                      style={{ color: 'var(--text-muted)' }}>
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="1.8"
                        strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                      </svg>
                      {detailedPdfDownloading
                        ? (t('common.loading'))
                        : (t('organise.detailed_pdf_with_cover'))}
                    </button>
                  )}
                  {/* v0.73e Finding 2: clear-all-allocations action.
                      Tucked at the bottom of the overflow menu so it's
                      not easy to misclick — destructive operation. Gated
                      on isAdmin && !isOverview (overview is read-only).
                      Confirmation overlay required before the actual
                      clear; the existing api_clear_category endpoint
                      handles the unconfirm-if-confirmed lifecycle. */}
                  {isAdmin && !isOverview && (
                    <button
                      onClick={async () => {
                        setShowOverflowMenu(false);
                        const ok = await confirm({
                          title: t('organise.clear_all_confirm.title'),
                          message: t('organise.clear_all_confirm.body', { category: category.name }),
                          confirmLabel: t('organise.clear_all_confirm.cta'),
                          danger: true,
                        });
                        if (!ok) return;
                        try {
                          await catApi.clear(eventId, category.id);
                          await loadAll();
                          if (onDataChange) onDataChange();
                          showToast(t('organise.clear_all.success'), 'success');
                        } catch (err) { showToast(err, 'error'); }
                      }}
                      className="w-full text-left px-4 py-2 text-xs hover:bg-black/5 dark:hover:bg-white/10"
                      style={{ color: 'var(--alert-burgundy)', borderTop: '1px solid var(--card-border)' }}>
                      {t('organise.clear_all.cta')}
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* v0.70d-2e-3 (AB3 Q2 composed transition): "ready to
            confirm" moment. Appears when the category is fully
            allocated but not yet confirmed (see isReadyToConfirm
            derivation above for the full condition set). Mirrors
            S3's gate card pattern in SetupHub — brighter io-accent
            tint + a primary CTA, with a one-time fade-in/scale
            flash on the false→true transition. The .gate-flash
            class is reused (the moment vocabulary is identical).
            Sits ABOVE the stats row so the existing readout
            ("✓ Alle zugeteilt" inline pill) isn't visually
            competing — the panel adds a new layer of meaning, it
            doesn't replace existing signal. After the user clicks
            Confirm, this panel disappears (category.confirmed
            flips true) and the existing confirmed banner above
            takes over (now AB4-augmented with directional hint). */}
        {isReadyToConfirm && (
          <div
            className={`flex items-center justify-between gap-3 rounded-card px-3 py-2 mb-3 flex-wrap ${readyFlashing ? 'gate-flash' : ''}`}
            style={{
              background: 'rgba(70,130,180,0.15)',
              border: '1px solid rgba(70,130,180,0.35)',
            }}
          >
            <div className="flex items-center gap-2 min-w-0">
              <span style={{ color: 'var(--io-accent)' }} aria-hidden="true">●</span>
              <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                {t('alloc.ready.title')}
              </span>
              <span className="text-[11px]" style={{ color: 'var(--text-subtle)' }}>
                {t('alloc.ready.hint')}
              </span>
            </div>
            {isAdmin && (
              <button
                type="button"
                onClick={handleConfirmCategory}
                disabled={confirming}
                className="text-xs font-semibold px-3 py-1.5 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 disabled:opacity-40 whitespace-nowrap shrink-0"
              >
                {confirming
                  ? (t('alloc.cta.confirming'))
                  : (t('alloc.ready.cta'))}
              </button>
            )}
            {confirmError && (
              <p className="w-full text-xs" style={{ color: 'var(--alert-burgundy)' }}>{formatErrorMessage(confirmError, t).primary}</p>
            )}
          </div>
        )}

        {/* Stats row */}
        <div className="flex items-center justify-between mb-1.5 flex-wrap gap-2">
          <div className="flex items-center gap-4 flex-wrap">
            <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
              <span className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>{totalOccupied}</span>
              <span style={{ color: 'var(--text-subtle)' }}>{isOverlapping ? ' ' + t('organise.assignments') : `/${activeParticipants.length} ` + t('organise.assigned')}</span>
            </span>
            {!isOverlapping && unassigned.length > 0 && <span className="text-sm font-medium text-pending">{unassigned.length} {t('organise.unassigned')}</span>}
            {!isOverlapping && unassigned.length === 0 && activeParticipants.length > 0 && <span className="text-sm font-medium" style={{ color: 'var(--io-accent)' }}>✓ {t('organise.everyone_assigned')}</span>}
            <span className="text-xs" style={{ color: 'var(--text-subtle)' }}>{units.length} × {itemLabel}</span>
          </div>
          <div className="flex items-center gap-2">
            {isAdmin && !isOverview && (
              <button onClick={() => setManageUnitsOpen(p => !p)}
                className="text-xs font-semibold hover:underline flex items-center gap-1"
                style={{ color: 'var(--io-accent)' }}>
                <span style={{ display: 'inline-block', transform: manageUnitsOpen ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s' }}>▶</span>
                {t('organise.manage_units', { item: itemLabel })}
              </button>
            )}
          {/* Overview: keep print button visible */}
          {isOverview && (
            <button onClick={() => window.print()}
              className="text-xs rounded-card px-3 py-1.5 border hover:bg-black/5 dark:hover:bg-white/10"
              style={{ color: 'var(--text-muted)', borderColor: 'var(--card-border)' }}>
              {t('organise.print')}
            </button>
          )}
          </div>
        </div>
        {!isOverlapping && (() => {
          // v0.70d-2d-2 (AB9): hoist progress percent so it can drive
          // both the fill width and the gradient's background-size. See
          // CheckInPanel for the same pattern — gradient stays anchored
          // to the full bar; <50% shows neutral, ≥50% reveals io-accent.
          const pct = activeParticipants.length > 0
            ? Math.min(100, Math.round((totalOccupied / activeParticipants.length) * 100))
            : 0;
          return (
            <div className="w-full rounded-full h-2" style={{ background: 'var(--card-border)' }}>
              <div className="rounded-full h-2 transition-all duration-300"
                style={{
                  width: `${pct}%`,
                  backgroundImage: 'linear-gradient(to right, rgba(120,120,120,0.55) 0%, rgba(120,120,120,0.55) 50%, var(--io-accent) 100%)',
                  backgroundSize: pct > 0 ? `${10000 / pct}% 100%` : '100% 100%',
                  backgroundRepeat: 'no-repeat',
                }} />
            </div>
          );
        })()}
      </div>

      {/* Category notes — only when showNotes */}
      {showNotes && catNotes.length > 0 && (
        <div className="mb-4 space-y-1">
          {catNotes.map(n => (
            <div key={n.id}
              className="rounded px-3 py-1.5 text-[11px] italic"
              style={{
                color: 'var(--text-subtle)',
                borderLeft: `2px solid ${n.is_published ? 'rgba(70,130,180,0.3)' : 'var(--card-border)'}`,
                background: n.is_published ? 'rgba(70,130,180,0.04)' : 'rgba(0,0,0,0.02)',
              }}>
              <span className="font-semibold not-italic text-[9px] uppercase tracking-caps mr-1.5" style={{ color: 'var(--text-subtle)' }}>
                {n.is_published ? t('notes.team') : t('notes.private')}
              </span>
              {truncate(n.content)}
            </div>
          ))}
        </div>
      )}

      {/* Create unit form */}
      {/* ── Collapsible: Manage Units ── */}
      {isAdmin && !isOverview && manageUnitsOpen && (
        <div
          className="rounded-2xl p-4 mb-4 space-y-3"
          style={{ background: 'var(--app-bg)', border: '1px solid var(--card-border)' }}>
          {/* Existing units list */}
          {units.length > 0 && (
            <div className="space-y-1.5">
              {units.map((unit, idx) => (
                <div key={unit.id}>
                  {editingUnit?.id === unit.id ? (
                    <div
                      className="card-surface-solid rounded-card p-3"
                      style={{
                        borderTop: '1px solid var(--card-border)',
                        borderRight: '1px solid var(--card-border)',
                        borderBottom: '1px solid var(--card-border)',
                        borderLeft: '3px solid var(--io-accent)',
                      }}>
                      <form onSubmit={handleUpdateUnit} className="space-y-2">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-semibold" style={{ color: 'var(--io-accent)' }}>
                            {t('organise.editing', { name: editingUnit.name })}
                          </span>
                          <button type="button" onClick={() => setEditingUnit(null)}
                            className="text-xs hover:underline"
                            style={{ color: 'var(--text-subtle)' }}>
                            {t('common.cancel')}
                          </button>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          <input type="text" value={editingUnit.name} onChange={e => setEditingUnit(p => ({ ...p, name: e.target.value }))}
                            className="rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]" />
                          <input type="text" placeholder={t('events.description')} value={editingUnit.description || ''} onChange={e => setEditingUnit(p => ({ ...p, description: e.target.value }))}
                            className="rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]" />
                        </div>
                        <div className="flex gap-2 flex-wrap">
                          {category.has_capacity && (
                            <input type="number" min="1" value={editingUnit.capacity || ''} placeholder={t('organise.capacity')}
                              onChange={e => setEditingUnit(p => ({ ...p, capacity: e.target.value }))}
                              className="w-24 rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]" />
                          )}
                          {category.has_gender_restriction && (
                            <select value={editingUnit.gender_restriction || ''} onChange={e => setEditingUnit(p => ({ ...p, gender_restriction: e.target.value }))}
                              className="rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]">
                              <option value="">{t('common.mixed')}</option>
                              <option value="male">{t('common.male_only')}</option>
                              <option value="female">{t('common.female_only')}</option>
                            </select>
                          )}
                          <button type="submit"
                            className="text-xs font-semibold px-4 py-1.5 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80">
                            {t('common.save')}
                          </button>
                        </div>
                      </form>
                    </div>
                  ) : (
                    <div
                      className="card-surface-solid flex items-center justify-between rounded-card px-3 py-2"
                      style={{ border: '1px solid var(--card-border)' }}>
                      <div className="min-w-0">
                        <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{unit.name}</span>
                        {unit.capacity && <span className="text-[10px] ml-2" style={{ color: 'var(--text-subtle)' }}>cap {unit.capacity}</span>}
                        {unit.gender_restriction && <span className="text-[10px] ml-1" style={{ color: 'var(--text-subtle)' }}>{unit.gender_restriction}</span>}
                      </div>
                      <div className="flex gap-2 items-center shrink-0">
                        {/* v0.58e-1: reorder arrows — universal on mobile + desktop */}
                        <button
                          onClick={() => {
                            if (idx === 0) return;
                            handleReorderUnits(unit.id, units[idx - 1].id);
                          }}
                          disabled={idx === 0}
                          aria-label={t('organise.move_up')}
                          title={t('organise.move_up')}
                          className="text-sm leading-none px-1 disabled:opacity-20 hover:opacity-70"
                          style={{ color: 'var(--text-subtle)' }}>
                          ▲
                        </button>
                        <button
                          onClick={() => {
                            if (idx === units.length - 1) return;
                            handleReorderUnits(unit.id, units[idx + 1].id);
                          }}
                          disabled={idx === units.length - 1}
                          aria-label={t('organise.move_down')}
                          title={t('organise.move_down')}
                          className="text-sm leading-none px-1 disabled:opacity-20 hover:opacity-70"
                          style={{ color: 'var(--text-subtle)' }}>
                          ▼
                        </button>
                        <button onClick={() => setEditingUnit({ ...unit })}
                          className="text-[10px] font-semibold hover:underline ml-1"
                          style={{ color: 'var(--io-accent)' }}>
                          {t('common.edit')}
                        </button>
                        <button onClick={() => handleDeleteUnit(unit.id)}
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
          {/* Add new unit. v1.0.0e: when there are no units yet, the
              add-area renders as a prominent dashed-border CTA card so
              the user's eye lands on it after clicking "Manage" on the
              far-right header (previously the small text-link was
              easy to miss on a wide viewport). When units exist, keep
              the subtle inline link — the unit cards above already
              anchor the eye and an aggressive CTA below them would
              clutter the surface. */}
          {!showCreate ? (
            units.length === 0 ? (
              <button
                type="button"
                onClick={() => setShowCreate(true)}
                className="block w-full rounded-card text-center py-6 text-sm font-semibold transition-colors"
                style={{
                  border: '2px dashed var(--card-border)',
                  background: 'transparent',
                  color: 'var(--io-accent)',
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--io-accent)'; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--card-border)'; }}>
                {t('organise.empty_units.cta', { item: itemLabel })}
              </button>
            ) : (
              <button onClick={() => setShowCreate(true)}
                className="text-xs font-semibold hover:underline"
                style={{ color: 'var(--io-accent)' }}>
                + {t('organise.new_unit', { item: itemLabel })}
              </button>
            )
          ) : (
            <div
              className="card-surface-solid rounded-card p-3"
              style={{ border: '1px solid var(--card-border)' }}>
              <form onSubmit={handleCreate} className="space-y-2">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>
                    {t('organise.new_unit', { item: itemLabel })}
                  </span>
                  <button type="button" onClick={() => setShowCreate(false)}
                    className="text-xs hover:underline"
                    style={{ color: 'var(--text-subtle)' }}>
                    {t('common.cancel')}
                  </button>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <input type="text" placeholder={`${itemLabel} ${t('common.name')} *`} value={form.name}
                    onChange={e => setForm(p => ({ ...p, name: e.target.value }))} required
                    className="rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]" />
                  <input type="text" placeholder={t('events.description')} value={form.description}
                    onChange={e => setForm(p => ({ ...p, description: e.target.value }))}
                    className="rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]" />
                </div>
                <div className="flex gap-2 flex-wrap">
                  {category.has_capacity && (
                    <input type="number" min="1" value={form.capacity} placeholder={t('organise.capacity')}
                      onChange={e => setForm(p => ({ ...p, capacity: e.target.value }))}
                      className="w-24 rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]" />
                  )}
                  {category.has_gender_restriction && (
                    <select value={form.gender_restriction} onChange={e => setForm(p => ({ ...p, gender_restriction: e.target.value }))}
                      className="rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]">
                      <option value="">{t('common.mixed')}</option>
                      <option value="male">{t('common.male_only')}</option>
                      <option value="female">{t('common.female_only')}</option>
                    </select>
                  )}
                  <button type="submit"
                    className="text-xs font-semibold px-4 py-1.5 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80">
                    {t('common.create')}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      )}

      {/* ═══ TWO-PANEL LAYOUT ═══ */}
      <div className="flex flex-col md:flex-row gap-4">

        {/* ─── LEFT: People Panel (hidden in setup mode) ─── */}
        {(
        <div ref={leftPanelRef}
          className="card-surface-solid w-full md:w-64 md:shrink-0 rounded-2xl flex flex-col"
          style={{ border: '1px solid var(--card-border)' }}
          onDragOver={e => { e.preventDefault(); setDragOverUnit('unassigned'); }}
          onDragLeave={() => setDragOverUnit(null)}
          onDrop={e => { e.preventDefault(); handleDropUnassigned(); }}>

          <div className="p-3 space-y-2 shrink-0" style={{ borderBottom: '1px solid var(--card-border)' }}>
            <div className="relative">
              <input type="text" value={search} onChange={e => setSearch(e.target.value)}
                placeholder={t('organise.search_panel')}
                className="w-full rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] pl-7 pr-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]" />
              <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[10px]" style={{ color: 'var(--text-subtle)' }}>🔍</span>
            </div>
            <div className="flex gap-1">
              {['', 'male', 'female'].map(g => (
                <button key={g} onClick={() => setGenderFilter(genderFilter === g ? '' : g)}
                  className={`text-[10px] px-2 py-0.5 rounded-full transition-colors ${
                    genderFilter === g
                      ? 'bg-steel-blue text-white dark:bg-gold dark:text-deep-navy'
                      : 'hover:bg-black/5 dark:hover:bg-white/10'
                  }`}
                  style={genderFilter === g ? undefined : {
                    background: 'rgba(128,128,128,0.10)',
                    color: 'var(--text-muted)',
                  }}>
                  {g === '' ? t('common.all') : g === 'male' ? t('people.gender.male') : t('people.gender.female')}
                </button>
              ))}
            </div>
          </div>

          <div className="px-3 py-2 flex items-center justify-between shrink-0" style={{ borderBottom: '1px solid var(--card-border)' }}>
            <span className="text-xs font-semibold" style={{ color: isOverlapping ? 'var(--io-accent)' : 'var(--pending-color)' }}>
              {leftPanelLabel}
              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full ml-1"
                style={isOverlapping
                  ? { background: 'var(--accent-tint)', color: 'var(--io-accent)' }
                  : { background: 'var(--pending-tint)', color: 'var(--pending-color)' }}>
                {leftPanelCount}
              </span>
              {/* v0.73b Q2: when ≥1 of the unassigned are pending, surface
                  the split inline so "N nicht zugewiesen" doesn't look
                  like the engine ignored confirmed participants. */}
              {!isOverlapping && pendingCount > 0 && (
                <span className="text-[10px] font-medium ml-2" style={{ color: 'var(--text-subtle)' }}>
                  ({t('organise.unassigned_pending_split', { pending: pendingCount })})
                </span>
              )}
            </span>
          </div>

          <div
            className="p-1.5 space-y-0.5 transition-colors"
            style={{
              // v0.60b-1: minHeight keeps the column visually stable
              // when the number of unassigned fluctuates (was jumping
              // taller/shorter 1→4 entries). maxHeight is the backstop
              // once it's genuinely crowded.
              minHeight: '24rem',
              maxHeight: '70vh',
              overflowY: 'auto',
              WebkitOverflowScrolling: 'touch',
              overscrollBehavior: 'contain',
              ...(dragOverUnit === 'unassigned' ? {
                background: 'var(--pending-tint)',
                boxShadow: 'inset 0 0 0 2px var(--pending-border)',
              } : {}),
            }}>
            {filteredLeftPanel.length === 0 ? (
              <div className="p-4 text-center">
                {leftPanelPeople.length === 0
                  ? <p className="text-[11px] font-medium" style={{ color: 'var(--io-accent)' }}>✓ {isOverlapping ? t('organise.no_participants_yet') : t('organise.everyone_assigned')}</p>
                  : <p className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>{t('common.no_matches')}</p>}
              </div>
            ) : sortedLeftPanel.map(p => {
              const pid = String(p.id);
              const isSel = selectedPeople.has(pid);
              const isAssigned = allAssignedIds.has(pid);
              const inUnits = isOverlapping ? units.filter(u => (allMembers[String(u.id)] || []).some(m => m.participant_id === pid)).map(u => u.name) : [];
              const pMarks = getParticipantMarks(p.id, 'organise');
              return (
                <div key={p.id}
                  draggable={HAS_FINE_POINTER}
                  onDragStart={HAS_FINE_POINTER ? () => {
                    setDragParticipant(selectedPeople.size > 0 && selectedPeople.has(pid) ? { id: pid, bulk: [...selectedPeople] } : { id: pid });
                    setDragSource('unassigned');
                  } : undefined}

                  onClick={() => toggleSelect(pid)}
                  className="flex items-center gap-2 px-2 py-1.5 rounded-card cursor-pointer transition-all text-xs hover:bg-black/5 dark:hover:bg-white/10"
                  style={{
                    color: 'var(--text-primary)',
                    ...(isSel
                      ? { background: 'rgba(70,130,180,0.12)', boxShadow: 'inset 0 0 0 1px var(--io-accent)' }
                      : isAssigned && !isOverlapping
                        ? { opacity: 0.4 }
                        : {}),
                  }}>
                  <div className="min-w-0 flex-1">
                    <div className="font-medium truncate flex items-center gap-0.5">
                      {p.first_name} {p.last_name}
                      <MarkDots marksForParticipant={pMarks} compact
                        onManage={!isMobileView ? () => setMarkModal(p) : undefined} />
                      {/* v0.73b Q1: pending pill — quiet grey badge so the
                          organiser knows at a glance which participants
                          haven't confirmed their email yet. The engine
                          still allocates them by default (controlled by
                          the include_pending toggle in the gear popover),
                          so the pill is informational, not blocking. */}
                      {p.registration_status === 'pending' && (
                        <span
                          className="text-[9px] font-semibold uppercase tracking-caps px-1.5 py-0.5 rounded-full ml-1 shrink-0"
                          title={t('organise.pending_pill.tooltip')}
                          style={{
                            background: 'rgba(128,128,128,0.14)',
                            color: 'var(--text-subtle)',
                          }}>
                          {t('organise.pending_pill')}
                        </span>
                      )}
                    </div>
                    <div className="flex gap-2 text-[10px]" style={{ color: 'var(--text-subtle)' }}>
                      {p.gender && <span>{p.gender === 'male' ? '♂' : '♀'}</span>}
                      {p.group_code && <span className="font-mono">{p.group_code}</span>}
                      {inUnits.length > 0 && <span className="truncate" style={{ color: 'var(--io-accent)' }}>in {inUnits.join(', ')}</span>}
                    </div>
                  </div>
                  {isSel && <span className="w-2 h-2 rounded-full shrink-0" style={{ background: 'var(--io-accent)' }} />}
                  <button
                    onClick={(e) => { e.stopPropagation(); setInsightParticipant(p); }}
                    aria-label={t('insight.open')}
                    title={t('insight.open')}
                    className="shrink-0 text-[12px] leading-none px-1 opacity-40 dark:opacity-70 hover:opacity-100 transition-opacity"
                    style={{ color: 'var(--text-subtle)' }}>
                    ⓘ
                  </button>
                </div>
              );
            })}
          </div>
        </div>
        )}

        {/* ─── RIGHT: Allocation Board ─── */}
        <div ref={rightPanelRef} className="flex-1 min-w-0">
          {units.length === 0 && !showCreate ? (
            <div
              className="rounded-2xl p-12 text-center"
              style={{
                background: 'var(--app-bg)',
                border: '1px solid var(--card-border)',
                color: 'var(--text-subtle)',
              }}>
              <p className="text-sm mb-1">{t('organise.no_units', { item: itemLabel })}</p>
              <p className="text-xs">{t('organise.no_units.hint')}</p>
              {isAdmin && (
                <button onClick={() => { setManageUnitsOpen(true); setShowCreate(true); }}
                  className="mt-3 text-xs font-semibold hover:underline"
                  style={{ color: 'var(--io-accent)' }}>
                  {t('organise.create_first', { item: itemLabel.toLowerCase() })}
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {units.map(unit => {
                const unitMembers = allMembers[String(unit.id)] || [];
                const nc = getNoteCount('unit', unit.id);
                const uNotes = showNotes ? (unitNotes[String(unit.id)] || []) : [];
                const dropValid = isDropValid(unit.id);
                const isOver = dragOverUnit === unit.id;

                // v0.50d-5i: compute unit-card style inline so theme tokens
                // resolve correctly. Drag-hover states mix Gold (reorder),
                // Steel Blue/Gold (valid drop), Burgundy tint (invalid drop),
                // and card-border (default).
                const unitStyle = (() => {
                  if (dragOverUnitId === unit.id) {
                    return { borderColor: '#FFD700', background: 'rgba(255,215,0,0.05)', boxShadow: '0 4px 12px rgba(0,0,0,0.15)' };
                  }
                  if (selectedPeople.size > 0) {
                    return { borderColor: 'var(--card-border)' };
                  }
                  if (isOver && dropValid) {
                    return { borderColor: 'var(--io-accent)', background: 'rgba(70,130,180,0.06)', boxShadow: '0 4px 12px rgba(0,0,0,0.15)' };
                  }
                  if (dragOverUnit === 'invalid-' + unit.id) {
                    return { borderColor: 'rgba(128,0,32,0.3)', background: 'rgba(128,0,32,0.05)' };
                  }
                  return { borderColor: 'var(--card-border)' };
                })();

                return (
                  <div key={unit.id}
                    draggable={isAdmin && selectedPeople.size === 0 && HAS_FINE_POINTER}
                    onDragStart={isAdmin && selectedPeople.size === 0 && HAS_FINE_POINTER ? (e) => { e.stopPropagation(); setDragUnitId(unit.id); } : undefined}
                    onClick={() => selectedPeople.size > 0 && !dragUnitId && handleUnitCardClick(unit)}
                    onDragOver={e => {
                      e.preventDefault();
                      if (dragUnitId && dragUnitId !== unit.id) { setDragOverUnitId(unit.id); return; }
                      if (dropValid) setDragOverUnit(unit.id); else setDragOverUnit('invalid-' + unit.id);
                    }}
                    onDragLeave={() => { setDragOverUnit(null); setDragOverUnitId(null); }}
                    onDrop={e => { e.preventDefault(); setDragOverUnit(null); setDragOverUnitId(null); if (dragUnitId && dragUnitId !== unit.id) { handleReorderUnits(dragUnitId, unit.id); return; } if (dropValid) handleDrop(unit.id); else showToast(t('organise.drop_here') + ' — ' + (category.has_capacity && unit.capacity && unit.occupant_count >= unit.capacity ? t('organise.full') : t('organise.rule_violation')), 'error'); }}
                    className="card-surface-solid rounded-2xl transition-all group flex flex-col"
                    style={{ borderWidth: '2px', borderStyle: 'solid', ...unitStyle, cursor: selectedPeople.size > 0 ? 'pointer' : undefined }}>

                    <div className="px-3 pt-3 pb-2">
                      {isAdmin && HAS_FINE_POINTER && (
                        <div className="flex items-center gap-1.5 mb-1 opacity-0 group-hover:opacity-100 transition-opacity cursor-grab active:cursor-grabbing select-none">
                          <span className="text-xs" style={{ color: 'var(--text-subtle)', opacity: 0.5 }}>⠿⠿</span>
                          <span className="text-[9px] uppercase tracking-caps" style={{ color: 'var(--text-subtle)', opacity: 0.7 }}>
                            {t('common.drag_to_reorder')}
                          </span>
                        </div>
                      )}
                      <div className="flex items-start justify-between mb-1">
                        {/* v1.0.0q: click-to-rename unit name. Admins
                            (and only in detail view, not overview)
                            click the title → input → Enter or blur
                            commits, Esc reverts. Falls back to the
                            full edit form via the "Bearbeiten" / Edit
                            button for capacity / gender / description. */}
                        {isAdmin && !isOverview && editingUnitRenameId === unit.id ? (
                          <input
                            type="text"
                            autoFocus
                            value={unitRenameDraft}
                            onChange={e => setUnitRenameDraft(e.target.value)}
                            onBlur={() => commitInlineRenameUnit(unit.id)}
                            onKeyDown={e => {
                              if (e.key === 'Enter') { e.preventDefault(); commitInlineRenameUnit(unit.id); }
                              else if (e.key === 'Escape') { e.preventDefault(); cancelInlineRenameUnit(); }
                            }}
                            className="font-heading font-bold text-sm bg-transparent border-b focus:outline-none focus:border-steel-blue truncate"
                            style={{
                              color: 'var(--text-primary)',
                              borderColor: 'var(--io-accent)',
                              minWidth: '140px',
                            }}
                          />
                        ) : (
                          <h4
                            onClick={isAdmin && !isOverview ? (e) => { e.stopPropagation(); startInlineRenameUnit(unit); } : undefined}
                            title={isAdmin && !isOverview ? t('organise.title_click_to_rename') : undefined}
                            className={`font-heading font-bold text-sm truncate ${isAdmin && !isOverview ? 'cursor-text hover:underline decoration-dotted decoration-1 underline-offset-4' : ''}`}
                            style={{ color: 'var(--text-primary)' }}>
                            {unit.name}
                          </h4>
                        )}
                        {(() => {
                          // v0.50d-5i: capacity pill — inline colour via capColor helper
                          // or neutral tint for overlapping (no-capacity) mode.
                          // v0.54: when overbooked (occupant_count > capacity) we also
                          // render a small burgundy label "over capacity" next to the
                          // pill so the signal is unambiguous at a glance, not just a
                          // colour shift.
                          const hasCap = category.has_capacity && unit.capacity;
                          const pillClass = hasCap
                            ? capColor(unit.occupant_count, unit.capacity)
                            : '';
                          const pillStyle = hasCap
                            ? undefined
                            : { background: 'rgba(128,128,128,0.12)', color: 'var(--text-muted)' };
                          const overbooked = hasCap && unit.occupant_count > unit.capacity;
                          return (
                            <span className="flex items-center gap-1.5 shrink-0 ml-2">
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${pillClass}`}
                                style={pillStyle}>
                                {hasCap ? `${unit.occupant_count}/${unit.capacity}` : unit.occupant_count}
                              </span>
                              {overbooked && (
                                <span className="text-[10px] font-semibold whitespace-nowrap"
                                  style={{ color: 'var(--alert-burgundy)' }}>
                                  {t('organise.over_capacity')}
                                </span>
                              )}
                            </span>
                          );
                        })()}
                      </div>
                      {(unit.gender_restriction || unit.description) && (
                        <div className="flex gap-2 text-[10px]" style={{ color: 'var(--text-subtle)' }}>
                          {unit.gender_restriction && <span>{t('organise.only', { gender: unit.gender_restriction })}</span>}
                          {unit.description && <span className="truncate">{unit.description}</span>}
                        </div>
                      )}
                    </div>

                    {/* Participants — ABOVE notes */}
                    <div className="px-3 pb-2 space-y-0.5 min-h-[32px]">
                      {unitMembers.length === 0 ? (
                        <div className="text-center py-3">
                          <p className="text-[10px] italic" style={{ color: 'var(--text-subtle)' }}>
                            {selectedPeople.size > 0 ? `Click to assign ${t('organise.selected', { n: selectedPeople.size })}` : t('organise.drop_here')}
                          </p>
                        </div>
                      ) : unitMembers.map(m => {
                        const mSel = selectedPeople.has(m.participant_id);
                        const mParticipant = findParticipant(m.participant_id);
                        const mMarks = getParticipantMarks(m.participant_id, 'organise');
                        return (
                          <div key={m.participant_id}
                            draggable={HAS_FINE_POINTER}
                            onDragStart={HAS_FINE_POINTER ? (e) => {
                              e.stopPropagation();
                              setDragParticipant(selectedPeople.size > 0 && selectedPeople.has(m.participant_id)
                                ? { id: m.participant_id, bulk: [...selectedPeople] }
                                : { id: m.participant_id });
                              setDragSource(unit.id);
                            } : undefined}

                            onClick={(e) => { e.stopPropagation(); toggleSelect(m.participant_id); }}
                            className="flex items-center justify-between group text-xs rounded-card px-2 py-1 cursor-pointer transition-colors"
                            style={mSel
                              ? { background: 'rgba(70,130,180,0.12)', boxShadow: 'inset 0 0 0 1px var(--io-accent)', color: 'var(--text-primary)' }
                              : { background: 'rgba(0,0,0,0.03)', color: 'var(--text-primary)' }}
                            onMouseEnter={e => { if (!mSel) e.currentTarget.style.background = 'rgba(0,0,0,0.06)'; }}
                            onMouseLeave={e => { if (!mSel) e.currentTarget.style.background = 'rgba(0,0,0,0.03)'; }}>
                            <span className="truncate flex items-center gap-0.5">
                              <span
                                title={mParticipant?.registration_status === 'pending' ? t('organise.pending_pill.tooltip') : undefined}
                                style={mParticipant?.registration_status === 'pending'
                                  ? { fontStyle: 'italic', color: 'var(--text-muted)' }
                                  : undefined}>
                                {m.participant_name}
                              </span>
                              <MarkDots marksForParticipant={mMarks} compact
                                onManage={!isMobileView && mParticipant ? () => setMarkModal(mParticipant) : undefined} />
                            </span>
                            <div className="flex items-center gap-1 shrink-0 ml-1">
                              {mSel && <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--io-accent)' }} />}
                              {mParticipant && (
                                <button
                                  onClick={(e) => { e.stopPropagation(); setInsightParticipant(mParticipant); }}
                                  aria-label={t('insight.open')}
                                  title={t('insight.open')}
                                  className="text-[11px] leading-none px-0.5 opacity-40 dark:opacity-70 hover:opacity-100 transition-opacity"
                                  style={{ color: 'var(--text-subtle)' }}>
                                  ⓘ
                                </button>
                              )}
                              {isAdmin && !mSel && (
                                <button onClick={(e) => { e.stopPropagation(); handleUnassign(unit.id, m.participant_id); }}
                                  className="text-[10px] opacity-0 group-hover:opacity-100 hover:underline"
                                  style={{ color: 'var(--alert-burgundy)' }}>✕</button>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Unit notes — BELOW participants, subdued */}
                    {uNotes.length > 0 && (
                      <div className="px-3 pb-2 space-y-0.5">
                        {uNotes.map(n => (
                          <div key={n.id} className="text-[10px] italic leading-tight pl-1"
                            style={{ color: 'var(--text-subtle)', borderLeft: '1px solid var(--card-border)' }}>
                            {truncate(n.content)}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* v0.70d-3c-9: card-action row uses icon-only at
                        ALL breakpoints. Previously sm:inline showed
                        text labels on >=640px viewport, but unit cards
                        live in a multi-column grid where each card
                        can be ~200-280px wide regardless of viewport.
                        German labels ("Notizen", "Löschen") overflowed
                        the card boundary. Icons + aria-label + title
                        keep the row clean and accessible.
                        v0.70d-2d-1 (AB1) was the prior partial fix. */}
                    <div className="flex items-center gap-3 px-3 py-2 rounded-b-2xl mt-auto"
                      style={{
                        borderTop: '1px solid var(--card-border)',
                        background: 'rgba(0,0,0,0.02)',
                      }}
                      onClick={e => e.stopPropagation()}>
                      <button onClick={() => setNotesFor({ type: 'unit', id: unit.id, name: unit.name })}
                        aria-label={t('common.notes')}
                        title={t('common.notes')}
                        className="text-[10px] font-semibold hover:underline inline-flex items-center"
                        style={{ color: 'var(--io-accent)' }}>
                        <span className="inline-flex" aria-hidden="true">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                            <polyline points="14 2 14 8 20 8" />
                            <line x1="8" y1="13" x2="16" y2="13" />
                            <line x1="8" y1="17" x2="13" y2="17" />
                          </svg>
                        </span>
                        {nc > 0 && (
                          <span className="ml-0.5 text-[8px] px-1 py-0 rounded-full"
                            style={{ background: 'var(--io-accent)', color: 'var(--card-bg-solid)' }}>
                            {nc}
                          </span>
                        )}
                      </button>
                      {isAdmin && (
                        <>
<button onClick={() => handleDeleteUnit(unit.id)}
                            aria-label={t('common.delete')}
                            title={t('common.delete')}
                            className="text-[10px] font-semibold hover:underline ml-auto inline-flex items-center"
                            style={{ color: 'var(--alert-burgundy)' }}>
                            <span className="inline-flex" aria-hidden="true">
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <polyline points="3 6 5 6 21 6" />
                                <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                                <path d="M10 11v6M14 11v6" />
                                <path d="M9 6V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2" />
                              </svg>
                            </span>
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Floating selection bar — v0.59a: bottom distance includes
          safe-area-inset-bottom so the bar clears the iOS home
          indicator. Non-notched devices get inset=0, so behaviour is
          unchanged there. */}
      {selectedPeople.size > 0 && (
        <div
          className="fixed bottom-[calc(1rem+env(safe-area-inset-bottom))] left-1/2 -translate-x-1/2 z-40 rounded-2xl px-5 py-3 flex items-center gap-3 flex-wrap justify-center"
          style={{
            background: '#0F1E2E',
            color: '#fff',
            boxShadow: '0 12px 40px rgba(0,0,0,0.5)',
          }}>
          <span className="text-sm font-medium">{t('organise.selected', { n: selectedPeople.size })}</span>
          <div className="relative">
            <button onClick={() => setAssignDropdown(!assignDropdown)}
              className="text-sm font-semibold px-4 py-1.5 rounded-card transition-colors bg-steel-blue hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80">
              {t('organise.assign_to')}
            </button>
            {assignDropdown && (
              <div
                className="card-surface-solid absolute bottom-full mb-2 left-0 rounded-card min-w-[180px] py-1 max-h-56 overflow-y-auto"
                style={{ border: '1px solid var(--card-border)', boxShadow: '0 12px 32px rgba(0,0,0,0.25)' }}>
                {units.map(u => {
                  const full = category.has_capacity && u.capacity && u.occupant_count >= u.capacity;
                  return (
                    <button key={u.id} disabled={full} onClick={() => handleBulkAssign(u.id)}
                      className="w-full text-left text-xs px-3 py-2 flex items-center justify-between hover:bg-black/5 dark:hover:bg-white/10 disabled:cursor-not-allowed"
                      style={{ color: full ? 'var(--text-subtle)' : 'var(--text-primary)' }}>
                      <span>{u.name}</span>
                      {u.capacity && (
                        <span className="text-[10px]"
                          style={{ color: full ? 'var(--alert-burgundy)' : 'var(--text-subtle)' }}>
                          {u.occupant_count}/{u.capacity}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
          <button onClick={handleBulkUnassign}
            className="text-sm font-semibold px-4 py-1.5 rounded-card transition-colors"
            style={{ background: 'rgba(255,255,255,0.1)' }}
            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.2)'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; }}>
            {t('organise.unassign')}
          </button>
          <button onClick={() => { setSelectedPeople(new Set()); setAssignDropdown(false); }}
            className="text-xs transition-colors hover:opacity-100"
            style={{ color: 'rgba(255,255,255,0.5)' }}
            onMouseEnter={e => { e.currentTarget.style.color = '#fff'; }}
            onMouseLeave={e => { e.currentTarget.style.color = 'rgba(255,255,255,0.5)'; }}>
            {t('organise.clear')}
          </button>
        </div>
      )}

      {notesFor && (
        <NotesModal entityType={notesFor.type} entityId={notesFor.id} entityName={notesFor.name}
          onClose={() => { setNotesFor(null); loadAll(); if (onDataChange) onDataChange(); }}
          isAdmin={isAdmin} />
      )}

      {markModal && (
        <MarkAssignModal
          participant={markModal}
          defs={markDefs}
          assignments={markAssignments}
          onAssign={async (markId, participantId) => { await assignMark(markId, participantId); }}
          onUnassign={async (markId, participantId) => { await unassignMark(markId, participantId); }}
          view="organise"
          canAssign={canAssignMarks}
          onClose={() => setMarkModal(null)} />
      )}

      {/* v0.58e: Participant insight panel (§6.2.2). v0.60b: threads
          isAdmin so the panel can conditionally render the admin-only
          allocation history section. */}
      <InsightPanel
        participant={insightParticipant}
        eventId={eventId}
        marksForPerson={insightParticipant ? getParticipantMarks(insightParticipant.id, 'organise') : []}
        isAdmin={isAdmin}
        participants={activeParticipants}
        onClose={() => setInsightParticipant(null)}
      />

      </>)}
      {/* v0.70d-1 R1: old proposal-review modal removed. ReviewSurface
          (rendered at the top of this return when `proposal` is set)
          supersedes it. The old modal was a centered overlay with a
          chip list; the new surface is in-place with Was/Will-be
          comparison and tap-for-reasons on every name. See
          R1-review-surface-spec.md for the full spec. */}

      <ConfirmOverlay />
    </div>
  );
}
