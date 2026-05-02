import { useState, useEffect, useMemo } from 'react';
import { users as usersApi, eventAssignments as assignApi } from '../services/api';
import { useConfirmOverlay } from './ConfirmOverlay';
import { useI18n } from '../hooks/useI18n';

import TranslatedError from './TranslatedError';
/**
 * EventAssignmentsPanel (v0.50e-1b)
 * ────────────────────────────────
 * Lists users assigned to this event and lets admins assign new users
 * with inline permissions. Permissions are per-user, per-event. The
 * "Copy permissions from" dropdown lets an admin seed the form with an
 * existing staff member's permissions to save clicks when onboarding
 * several staff with the same access pattern.
 *
 * Staff groups are gone — this used to have a whole second section for
 * defining named roles. That indirection is now unnecessary.
 */

export default function EventAssignmentsPanel({ eventId, isAdmin, onChange }) {
  const [allUsers, setAllUsers] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Assign/edit form state
  const [showAssign, setShowAssign] = useState(false);
  const [editingAssignmentId, setEditingAssignmentId] = useState(null);

  // v0.50f final permission shape: people (r/w/none), organise (r/w/none),
  // checkin (object: access + pre_event), reports (toggle), marks (r/w/none).
  // v1.0-pre #10: checkin promoted to {access, pre_event} so admins can
  // grant a staff member the new "before the event" access for pre-event
  // setup of check-in columns.
  const emptyPerms = () => ({
    people: '',
    organise: '',
    checkin: { access: '', pre_event: false },
    reports: '',
    marks: '',
  });

  const [assignForm, setAssignForm] = useState({
    user_id: '',
    role: 'staff',
    permissions: emptyPerms(),
  });

  const { confirm, ConfirmOverlay } = useConfirmOverlay();
  const { t } = useI18n();

  const PERM_OPTIONS = [
    { value: '', label: t('common.no_access') },
    { value: 'read', label: t('common.read_only') },
    { value: 'write', label: t('common.read_write') },
  ];

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { loadAll(); }, [eventId]);

  // v1.0-pre #10: reconcile checkin to the α-shape, accepting either
  // legacy flat-string ("write" or "" or null) or the new object form.
  // Defaulting pre_event to false for legacy values matches the migration.
  const reconcileCheckin = (raw) => {
    if (raw && typeof raw === 'object') {
      return { access: raw.access || '', pre_event: !!raw.pre_event };
    }
    return { access: raw || '', pre_event: false };
  };

  const reconcilePerms = (perms) => ({
    people:   perms.people   || '',
    organise: perms.organise || '',
    checkin:  reconcileCheckin(perms.checkin),
    reports:  perms.reports  || '',
    marks:    perms.marks    || '',
  });

  const loadAll = async () => {
    setLoading(true);
    try {
      const [users, assigns] = await Promise.all([
        usersApi.list(),
        assignApi.list(eventId),
      ]);
      setAllUsers(users);
      setAssignments(assigns);
    } catch (err) { setError(err); }
    finally { setLoading(false); }
  };

  // Users available for assignment: active users not already assigned.
  const assignableUsers = useMemo(() => {
    const assignedIds = new Set(assignments.map(a => a.user_id));
    return allUsers.filter(u => u.is_active && !assignedIds.has(u.id));
  }, [allUsers, assignments]);

  // Staff assignments (for "Copy from" dropdown) — event_admins have no
  // meaningful permissions to copy, so only show role=staff entries.
  const copyableAssignments = useMemo(
    () => assignments.filter(a => a.role === 'staff'),
    [assignments]
  );

  const handleStartAssign = () => {
    setShowAssign(true);
    setEditingAssignmentId(null);
    setAssignForm({ user_id: '', role: 'staff', permissions: emptyPerms() });
  };

  const handleStartEdit = (a) => {
    setEditingAssignmentId(a.id);
    setShowAssign(false);
    setAssignForm({
      user_id: a.user_id,
      role: a.role,
      permissions: reconcilePerms(a.permissions || {}),
    });
  };

  const handleCancel = () => {
    setShowAssign(false);
    setEditingAssignmentId(null);
    setError(null);
  };

  const handleCopyFrom = (sourceAssignmentId) => {
    const src = assignments.find(a => a.id === sourceAssignmentId);
    if (!src) return;
    setAssignForm(p => ({ ...p, permissions: reconcilePerms(src.permissions || {}) }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    // Clean the permissions payload: drop empty-string entries for tidiness.
    const cleanPerms = {};
    Object.entries(assignForm.permissions).forEach(([k, v]) => { if (v) cleanPerms[k] = v; });
    try {
      if (editingAssignmentId) {
        await assignApi.update(eventId, editingAssignmentId, {
          role: assignForm.role,
          permissions: cleanPerms,
        });
      } else {
        if (!assignForm.user_id) {
          setError(t('staff.assign.pick_user_error'));
          return;
        }
        await assignApi.create(eventId, {
          user_id: assignForm.user_id,
          role: assignForm.role,
          permissions: cleanPerms,
        });
      }
      setShowAssign(false);
      setEditingAssignmentId(null);
      await loadAll();
      // v0.70d-2e-2 (M0): notify parent so SetupHub's `assignments`
      // length-driven `confirmed` prop reflects changes (see M0 in
      // MarksPanel for the same pattern).
      onChange?.();
    } catch (err) { setError(err); }
  };

  const handleRemove = async (a) => {
    const ok = await confirm({
      title: t('staff.remove.title'),
      message: t('staff.remove.message', { name: a.user_full_name || a.user_email }),
      confirmLabel: t('common.remove'),
      tone: 'danger',
    });
    if (!ok) return;
    try {
      await assignApi.delete(eventId, a.id);
      await loadAll();
      onChange?.();
    } catch (err) { setError(err); }
  };

  const describePerms = (perms, role) => {
    if (role === 'event_admin') return t('staff.role.event_admin_full');
    if (!perms || Object.keys(perms).length === 0) return t('common.no_access');
    const parts = [];
    if (perms.people) parts.push(`${t('marks.views.people')}: ${perms.people}`);
    if (perms.organise) parts.push(`${t('nav.organise')}: ${perms.organise}`);
    if (perms.checkin && (typeof perms.checkin === 'object' ? perms.checkin.access : perms.checkin)) {
      parts.push(`${t('nav.checkin')}: ${t('common.enabled')}`);
    }
    if (perms.reports) parts.push(`${t('nav.reports')}: ${t('common.enabled')}`);
    if (perms.marks) parts.push(`${t('nav.marks')}: ${t('common.enabled')}`);
    return parts.join(' · ') || t('common.no_access');
  };

  // ── Styles ──
  const inputClass = "rounded-card border px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]";
  const inputStyle = {
    background: 'var(--app-bg)',
    borderColor: 'var(--card-border)',
    color: 'var(--text-primary)',
  };

  if (loading) {
    return <p className="text-sm" style={{ color: 'var(--text-subtle)' }}>{t('common.loading')}</p>;
  }

  const userName = (uid) => {
    const u = allUsers.find(x => x.id === uid);
    return u ? (u.full_name || u.email) : uid;
  };

  const AssignOrEditForm = () => {
    const submitLabel = editingAssignmentId
      ? t('common.save')
      : (t('staff.assign.submit'));
    const isStaffRole = assignForm.role === 'staff';

    return (
      <form
        onSubmit={handleSubmit}
        className="card-surface-solid rounded-2xl p-4 space-y-4 mb-4"
        style={{ border: '1px solid var(--card-border)' }}
      >
        <h3 className="font-heading font-bold text-sm" style={{ color: 'var(--text-primary)' }}>
          {editingAssignmentId
            ? (t('staff.edit.title'))
            : (t('staff.assign.title'))}
        </h3>

        {/* User picker — disabled when editing (user is fixed) */}
        <div>
          <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
            style={{ color: 'var(--text-subtle)' }}>
            {t('staff.assign.user_label')}
          </label>
          {editingAssignmentId ? (
            <p className="text-sm" style={{ color: 'var(--text-primary)' }}>
              {userName(assignForm.user_id)}
            </p>
          ) : (
            <select value={assignForm.user_id}
              onChange={e => setAssignForm(p => ({ ...p, user_id: e.target.value }))}
              required className={`w-full ${inputClass}`} style={inputStyle}>
              <option value="">{t('staff.assign.pick_user')}</option>
              {assignableUsers.map(u => (
                <option key={u.id} value={u.id}>
                  {u.full_name ? `${u.full_name} (${u.email})` : u.email}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Role */}
        <div>
          <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
            style={{ color: 'var(--text-subtle)' }}>
            {t('users.role')}
          </label>
          <select value={assignForm.role}
            onChange={e => setAssignForm(p => ({ ...p, role: e.target.value }))}
            className={`w-full ${inputClass}`} style={inputStyle}>
            <option value="staff">{t('role.staff')}</option>
            <option value="event_admin">{t('role.event_admin')}</option>
          </select>
          {assignForm.role === 'event_admin' && (
            <p className="text-[10px] mt-1" style={{ color: 'var(--text-subtle)' }}>
              {t('staff.role.event_admin_hint')}
            </p>
          )}
        </div>

        {/* Copy from — only shown for staff role AND when other staff exist */}
        {isStaffRole && copyableAssignments.length > 0 && (
          <div>
            <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
              style={{ color: 'var(--text-subtle)' }}>
              {t('staff.assign.copy_from')}
            </label>
            <select value=""
              onChange={e => { if (e.target.value) { handleCopyFrom(e.target.value); e.target.value = ''; } }}
              className={`w-full ${inputClass}`} style={inputStyle}>
              <option value="">{t('staff.assign.copy_from_placeholder')}</option>
              {copyableAssignments
                .filter(a => a.id !== editingAssignmentId)
                .map(a => (
                  <option key={a.id} value={a.id}>
                    {a.user_full_name || a.user_email}
                  </option>
                ))}
            </select>
            <p className="text-[10px] mt-1" style={{ color: 'var(--text-subtle)' }}>
              {t('staff.assign.copy_from_hint')}
            </p>
          </div>
        )}

        {/* Permissions — only for staff role */}
        {isStaffRole && (
          <div>
            <label className="block text-[10px] uppercase tracking-caps font-semibold mb-2"
              style={{ color: 'var(--text-subtle)' }}>
              {t('staff.assign.permissions')}
            </label>
            <div className="space-y-3">
              {/* People — read / write / none */}
              <div className="flex items-center gap-3">
                <span className="text-xs w-32 shrink-0" style={{ color: 'var(--text-muted)' }}>
                  {t('marks.views.people')}
                </span>
                <select value={assignForm.permissions.people || ''}
                  onChange={e => setAssignForm(p => ({ ...p, permissions: { ...p.permissions, people: e.target.value } }))}
                  className={inputClass} style={inputStyle}>
                  {PERM_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>

              {/* Allocation board — read / write / none */}
              <div className="flex items-center gap-3">
                <span className="text-xs w-32 shrink-0" style={{ color: 'var(--text-muted)' }}>
                  {t('nav.organise')}
                </span>
                <select value={assignForm.permissions.organise || ''}
                  onChange={e => setAssignForm(p => ({ ...p, permissions: { ...p.permissions, organise: e.target.value } }))}
                  className={inputClass} style={inputStyle}>
                  {PERM_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>

              {/* Marks — v0.50f-1: toggle (write / none). Read is implicit
                  with event access: anyone who can see participants can
                  see their marks, so there's no "read-only" state worth
                  configuring. Write is explicit. */}
              <div className="flex items-start gap-3">
                <span className="text-xs w-32 shrink-0 pt-1" style={{ color: 'var(--text-muted)' }}>
                  {t('nav.marks')}
                </span>
                <label className="flex items-start gap-2 cursor-pointer flex-1">
                  <input type="checkbox"
                    checked={!!assignForm.permissions.marks}
                    onChange={e => setAssignForm(p => ({
                      ...p,
                      permissions: { ...p.permissions, marks: e.target.checked ? 'write' : '' },
                    }))}
                    className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold mt-0.5" />
                  <div className="min-w-0">
                    <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
                      {t('staff.roles.perm.marks_label')}
                    </span>
                    <p className="text-[10px] mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                      {t('staff.roles.perm.marks_hint')}
                    </p>
                  </div>
                </label>
              </div>

              {/* Check-in — toggle, with v1.0-pre #10 sub-toggle for
                  pre-event access. The sub-toggle only renders when the
                  parent is ticked (1A shape). Submitting the form sends
                  the α-shape object {access, pre_event} regardless of
                  which sub-toggle state. */}
              <div className="flex items-start gap-3">
                <span className="text-xs w-32 shrink-0 pt-1" style={{ color: 'var(--text-muted)' }}>
                  {t('nav.checkin')}
                </span>
                <div className="flex-1 min-w-0">
                  <label className="flex items-start gap-2 cursor-pointer">
                    <input type="checkbox"
                      checked={!!assignForm.permissions.checkin?.access}
                      onChange={e => setAssignForm(p => ({
                        ...p,
                        permissions: {
                          ...p.permissions,
                          checkin: e.target.checked
                            ? { access: 'write', pre_event: !!p.permissions.checkin?.pre_event }
                            : { access: '', pre_event: false },
                        },
                      }))}
                      className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold mt-0.5" />
                    <div className="min-w-0">
                      <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
                        {t('staff.roles.perm.checkin_label')}
                      </span>
                      <p className="text-[10px] mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                        {t('staff.roles.perm.checkin_hint')}
                      </p>
                    </div>
                  </label>
                  {/* Sub-toggle — only when the parent is on */}
                  {assignForm.permissions.checkin?.access && (
                    <label className="flex items-start gap-2 cursor-pointer mt-2 ml-6">
                      <input type="checkbox"
                        checked={!!assignForm.permissions.checkin?.pre_event}
                        onChange={e => setAssignForm(p => ({
                          ...p,
                          permissions: {
                            ...p.permissions,
                            checkin: {
                              access: p.permissions.checkin?.access || 'write',
                              pre_event: e.target.checked,
                            },
                          },
                        }))}
                        className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold mt-0.5" />
                      <div className="min-w-0">
                        <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
                          {t('staff.roles.perm.checkin_pre_event_label')}
                        </span>
                        <p className="text-[10px] mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                          {t('staff.roles.perm.checkin_pre_event_hint')}
                        </p>
                      </div>
                    </label>
                  )}
                </div>
              </div>

              {/* Reports — toggle */}
              <div className="flex items-start gap-3">
                <span className="text-xs w-32 shrink-0 pt-1" style={{ color: 'var(--text-muted)' }}>
                  {t('nav.reports')}
                </span>
                <label className="flex items-start gap-2 cursor-pointer flex-1">
                  <input type="checkbox"
                    checked={!!assignForm.permissions.reports}
                    onChange={e => setAssignForm(p => ({
                      ...p,
                      permissions: { ...p.permissions, reports: e.target.checked ? 'read' : '' },
                    }))}
                    className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold mt-0.5" />
                  <div className="min-w-0">
                    <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
                      {t('staff.roles.perm.reports_label')}
                    </span>
                    <p className="text-[10px] mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                      {t('staff.roles.perm.reports_hint')}
                    </p>
                  </div>
                </label>
              </div>
            </div>
          </div>
        )}

        <TranslatedError err={error} variant="compact" />

        <div className="flex items-center gap-2">
          <button type="submit"
            className="text-xs font-semibold px-4 py-2 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80">
            {submitLabel}
          </button>
          <button type="button" onClick={handleCancel}
            className="text-xs font-medium px-2 py-2 hover:underline"
            style={{ color: 'var(--text-subtle)' }}>
            {t('common.cancel')}
          </button>
        </div>
      </form>
    );
  };

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-4 gap-3">
        <div className="min-w-0">
          <h2 className="font-heading font-bold text-lg" style={{ color: 'var(--text-primary)' }}>
            {t('staff.title')}
          </h2>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-subtle)' }}>
            {t('staff.subtitle')}
          </p>
        </div>
        {isAdmin && !showAssign && !editingAssignmentId && (
          <button onClick={handleStartAssign}
            className="text-xs font-semibold px-4 py-2 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 shrink-0">
            {t('staff.assign.new')}
          </button>
        )}
      </div>

      {/* Assign new form */}
      {showAssign && <AssignOrEditForm />}

      {/* Assignment list */}
      <div
        className="card-surface-solid rounded-2xl overflow-hidden"
        style={{ border: '1px solid var(--card-border)' }}
      >
        {assignments.length === 0 ? (
          <div className="p-8 text-center text-sm" style={{ color: 'var(--text-subtle)' }}>
            {t('staff.empty')}
          </div>
        ) : (
          <div>
            {assignments.map((a, i) => {
              const isEditing = editingAssignmentId === a.id;
              return (
                <div key={a.id} style={i > 0 ? { borderTop: '1px solid var(--card-border)' } : undefined}>
                  {isEditing ? (
                    <div className="p-3"><AssignOrEditForm /></div>
                  ) : (
                    <div className="flex items-start justify-between gap-3 px-4 py-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                            {a.user_full_name || a.user_email}
                          </span>
                          {(() => {
                            const roleStyle = a.role === 'event_admin'
                              ? { bg: 'rgba(70,130,180,0.14)', color: 'var(--io-accent)' }
                              : { bg: 'rgba(128,128,128,0.12)', color: 'var(--text-muted)' };
                            return (
                              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded"
                                style={{ background: roleStyle.bg, color: roleStyle.color }}>
                                {t('role.' + a.role)}
                              </span>
                            );
                          })()}
                          {a.user_is_active === false && (
                            <span className="text-[10px]" style={{ color: 'var(--text-subtle)' }}>
                              ({t('users.inactive')})
                            </span>
                          )}
                        </div>
                        {a.user_full_name && (
                          <p className="text-xs mt-0.5" style={{ color: 'var(--text-subtle)' }}>
                            {a.user_email}
                          </p>
                        )}
                        <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                          {describePerms(a.permissions, a.role)}
                        </p>
                      </div>
                      {isAdmin && (
                        <div className="flex gap-3 shrink-0">
                          <button onClick={() => handleStartEdit(a)}
                            className="text-xs font-semibold hover:underline"
                            style={{ color: 'var(--io-accent)' }}>
                            {t('common.edit')}
                          </button>
                          <button onClick={() => handleRemove(a)}
                            className="text-xs font-semibold hover:underline"
                            style={{ color: 'var(--alert-burgundy)' }}>
                            {t('common.remove')}
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <ConfirmOverlay />
    </div>
  );
}
