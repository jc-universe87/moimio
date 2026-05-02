import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { users as usersApi, events as eventsApi } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { useConfirmOverlay } from '../components/ConfirmOverlay';
import { useI18n } from '../hooks/useI18n';
import EmptyState from '../components/EmptyState';

import TranslatedError from '../components/TranslatedError';
export default function UserManagementPage() {
  const [userList, setUserList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({ full_name: '', email: '', password: '', role: 'staff', can_manage_users: false, can_create_events: false });
  const [editForm, setEditForm] = useState({});
  const { user: currentUser } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  // v0.50d-4b: if ?from={eventId} is present, we got here via an
  // in-event sidebar click — show a "Back to {event}" breadcrumb so
  // returning is one click. Fetch the event name for a friendlier label.
  const fromEventId = searchParams.get('from');
  const [fromEvent, setFromEvent] = useState(null);
  // v0.50j: system-level roles collapsed to Super Admin + Staff.
  // Per-event admin access lives on EventUserAssignment.role, not here.
  // Only Super Admin can create other Super Admins — not exposed in the
  // create form (seed via CLI or setup). The role dropdown therefore
  // only offers 'staff' in this UI; we keep the constant in case we
  // expose more roles in the future.
  const ROLE_OPTIONS = [
    { value: 'staff', label: t('role.staff') },
  ];
  const [showPw, setShowPw] = useState(false);
  const { confirm, ConfirmOverlay } = useConfirmOverlay();

  const isSuperAdmin = currentUser?.role === 'super_admin';

  useEffect(() => { loadUsers(); }, []);
  // v0.50d-4b: fetch the event name when we arrived via ?from={eventId}
  // so the breadcrumb reads "Back to {event name}" rather than a UUID.
  useEffect(() => {
    if (!fromEventId) { setFromEvent(null); return; }
    let cancelled = false;
    eventsApi.get(fromEventId)
      .then(ev => { if (!cancelled) setFromEvent(ev); })
      .catch(() => {}); // If the fetch fails, breadcrumb still works with the generic label.
    return () => { cancelled = true; };
  }, [fromEventId]);

  const loadUsers = async () => {
    try {
      const data = await usersApi.list();
      setUserList(data);
    } catch (err) { setError(err); }
    finally { setLoading(false); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await usersApi.create(form);
      setForm({ full_name: '', email: '', password: '', role: 'staff', can_manage_users: false, can_create_events: false });
      setShowCreate(false);
      await loadUsers();
    } catch (err) { setError(err); }
  };

  const handleUpdate = async (userId) => {
    setError(null);
    try {
      await usersApi.update(userId, editForm);
      setEditingId(null);
      await loadUsers();
    } catch (err) { setError(err); }
  };

  const handleDeactivate = async (u) => {
    const ok = await confirm({
      title: u.is_active ? t('users.deactivate.title', { name: u.full_name }) : t('users.reactivate') + ` ${u.full_name}`,
      message: u.is_active
        ? t('users.deactivate.message')
        : t('users.reactivate.message'),
      confirmLabel: u.is_active ? t('users.deactivate') : t('users.reactivate'),
      danger: u.is_active,
    });
    if (!ok) return;
    try {
      await usersApi.update(u.id, { is_active: !u.is_active });
      await loadUsers();
    } catch (err) { setError(err); }
  };

  const handleDelete = async (u) => {
    const ok = await confirm({
      title: t('users.delete.title', { name: u.full_name }),
      message: t('users.delete.message'),
      confirmLabel: t('users.delete.confirm'),
      danger: true,
    });
    if (!ok) return;
    try {
      await usersApi.delete(u.id);
      await loadUsers();
    } catch (err) { setError(err); }
  };

  const startEdit = (u) => {
    setEditingId(u.id);
    // v0.70d-3c-10a: include can_create_events. Pre-3c-10a this
    // field was omitted, which caused two compounding bugs:
    //   1. The edit form's "Kann neue Events erstellen" checkbox
    //      always rendered unchecked (because !!undefined === false),
    //      regardless of the user's actual DB value.
    //   2. Save sent editForm with can_create_events: undefined.
    //      JSON.stringify drops undefined, so the PATCH body never
    //      carried the field, and the backend's merge-patch
    //      (`if data.can_create_events is not None: ...`) left the
    //      column unchanged.
    // Net effect: any user with can_create_events=true in the DB
    // could not have it un-toggled via the UI. This bit users who
    // had been migrated from the old event_admin role in v0.50j —
    // that migration retroactively set can_create_events=true on
    // them, and there was no way to clear it from the UI.
    setEditForm({
      full_name: u.full_name,
      role: u.role,
      can_manage_users: u.can_manage_users,
      can_create_events: u.can_create_events,
      is_active: u.is_active,
    });
  };

  const inputClass = "rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]";

  if (loading) return <p className="text-sm" style={{ color: 'var(--text-subtle)' }}>{t('common.loading')}</p>;

  return (
    <div className="max-w-3xl">
      {/* v0.50d-4b: Back-to-event breadcrumb — only shown when we arrived
          via the in-event sidebar Users button. Returns to the event's
          default section (phase-appropriate landing). */}
      {fromEventId && (
        <button
          type="button"
          onClick={() => navigate(`/admin/events/${fromEventId}`)}
          className="inline-flex items-center gap-1 text-xs font-medium mb-3 hover:underline"
          style={{ color: 'var(--text-muted)' }}
        >
          {fromEvent?.name
            ? <>← {fromEvent.name}</>
            : t('users.back_to_event')}
        </button>
      )}
      {/* Header */}
      <div className="flex items-center justify-between mb-4 gap-3">
        <div className="min-w-0">
          <h2 className="font-heading text-xl font-bold" style={{ color: 'var(--text-primary)' }}>
            {t('users.title')}
          </h2>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-subtle)' }}>
            {t('users.subtitle')}
          </p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)}
          className="text-xs font-semibold px-4 py-2 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 shrink-0">
          {showCreate ? t('common.cancel') : t('users.new')}
        </button>
      </div>

      {/* Role descriptions */}
      <div
        className="rounded-2xl p-3 mb-5 space-y-2"
        style={{
          background: 'var(--app-bg)',
          border: '1px solid var(--card-border)',
        }}
      >
        <p className="text-[9px] uppercase tracking-caps font-semibold mb-1" style={{ color: 'var(--text-subtle)' }}>
          {t('users.role_ref')}
        </p>
        <div>
          <span className="text-[10px] font-semibold" style={{ color: 'var(--alert-burgundy)' }}>
            {t('role.super_admin')}
          </span>
          <span className="text-[10px] ml-2" style={{ color: 'var(--text-muted)' }}>
            {t('users.role_desc.super_admin')}
          </span>
        </div>
        <div>
          <span className="text-[10px] font-semibold" style={{ color: 'var(--text-primary)' }}>
            {t('role.staff')}
          </span>
          <span className="text-[10px] ml-2" style={{ color: 'var(--text-muted)' }}>
            {t('users.role_desc.staff')}
          </span>
        </div>
        {/* v0.50j: system-level capability flags that any Staff user can
            be granted. Per-event admin access is managed on each event's
            Staff & Permissions page, not here. */}
        <div className="pt-1 mt-1 border-t" style={{ borderColor: 'var(--card-border)' }}>
          <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
            <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
              {t('users.capabilities')}
            </span>
            {' · '}
            {t('users.capabilities.hint')}
          </p>
        </div>
      </div>

      <TranslatedError err={error} className="text-xs rounded-card p-3 mb-4" />

      {showCreate && (
        <div
          className="card-surface-solid rounded-2xl p-5 mb-5"
          style={{ border: '1px solid var(--card-border)' }}
        >
          <h3 className="font-heading font-bold text-sm mb-3" style={{ color: 'var(--text-primary)' }}>
            {t('users.create.title')}
          </h3>
          <form onSubmit={handleCreate} className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
                  style={{ color: 'var(--text-subtle)' }}>
                  {t('users.full_name')} *
                </label>
                <input type="text" value={form.full_name} onChange={e => setForm(p => ({ ...p, full_name: e.target.value }))}
                  required className={`w-full ${inputClass}`} />
              </div>
              <div>
                <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
                  style={{ color: 'var(--text-subtle)' }}>
                  {t('users.email')} *
                </label>
                <input type="email" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))}
                  required className={`w-full ${inputClass}`} />
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
                  style={{ color: 'var(--text-subtle)' }}>
                  {t('users.password')} *
                </label>
                <div className="relative">
                  <input type={showPw ? "text" : "password"} value={form.password} onChange={e => setForm(p => ({ ...p, password: e.target.value }))}
                    required className={`w-full pr-14 ${inputClass}`} />
                  <button type="button" onClick={() => setShowPw(v => !v)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] hover:underline"
                    style={{ color: 'var(--text-subtle)' }}>
                    {showPw ? t('common.hide') : t('common.show')}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-[10px] uppercase tracking-caps font-semibold mb-1"
                  style={{ color: 'var(--text-subtle)' }}>
                  {t('users.role')}
                </label>
                <select value={form.role} onChange={e => setForm(p => ({ ...p, role: e.target.value }))}
                  className={`w-full ${inputClass}`}>
                  {ROLE_OPTIONS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                  {isSuperAdmin && <option value="super_admin">{t('role.super_admin')}</option>}
                </select>
              </div>
            </div>
            {/* v0.50j: capability flags shown for any non-super role.
                Super Admin has both implicitly, so no need to expose
                them when super is selected. */}
            {form.role !== 'super_admin' && (
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-xs cursor-pointer" style={{ color: 'var(--text-muted)' }}>
                  <input type="checkbox" checked={form.can_manage_users}
                    onChange={e => setForm(p => ({ ...p, can_manage_users: e.target.checked }))}
                    className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold" />
                  {t('users.can_manage')}
                </label>
                <label className="flex items-center gap-2 text-xs cursor-pointer" style={{ color: 'var(--text-muted)' }}>
                  <input type="checkbox" checked={form.can_create_events}
                    onChange={e => setForm(p => ({ ...p, can_create_events: e.target.checked }))}
                    className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold" />
                  {t('users.can_create_events')}
                </label>
              </div>
            )}
            <button type="submit"
              className="text-xs font-semibold px-4 py-2 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80">
              {t('users.submit')}
            </button>
          </form>
        </div>
      )}

      <div
        className="card-surface-solid rounded-2xl overflow-hidden"
        style={{ border: '1px solid var(--card-border)' }}
      >
        <div className="overflow-x-auto" style={{ WebkitOverflowScrolling: 'touch' }}>
          {userList.length === 0 ? (
            <div className="p-5">
              <EmptyState
                compact
                title={t('users.empty.title')}
                hint={t('users.empty.hint')}
              />
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr
                  className="text-left text-[10px] uppercase tracking-caps font-semibold"
                  style={{
                    background: 'rgba(0,0,0,0.03)',
                    color: 'var(--text-subtle)',
                    borderBottom: '1px solid var(--card-border)',
                  }}>
                  <th className="px-4 py-2">{t('common.name')}</th>
                  <th className="px-4 py-2">{t('common.email')}</th>
                  <th className="px-4 py-2">{t('users.role')}</th>
                  <th className="px-4 py-2">{t('common.status')}</th>
                  <th className="px-4 py-2 text-right">{t('common.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {userList.map(u => (
                  <tr key={u.id}
                    className={`${!u.is_active ? 'opacity-50' : ''}`}
                    style={{ borderTop: '1px solid var(--card-border)' }}>
                    {editingId === u.id ? (
                      <>
                        <td className="px-4 py-2">
                          <input value={editForm.full_name} onChange={e => setEditForm(p => ({ ...p, full_name: e.target.value }))}
                            className={inputClass} style={{ width: '140px' }} />
                        </td>
                        <td className="px-4 py-2 text-xs" style={{ color: 'var(--text-subtle)' }}>{u.email}</td>
                        <td className="px-4 py-2">
                          <select value={editForm.role} onChange={e => setEditForm(p => ({ ...p, role: e.target.value }))}
                            className={inputClass} disabled={u.role === 'super_admin' && !isSuperAdmin}>
                            {ROLE_OPTIONS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                            {isSuperAdmin && <option value="super_admin">{t('role.super_admin')}</option>}
                          </select>
                        </td>
                        <td className="px-4 py-2">
                          {editForm.role !== 'super_admin' && (
                            <div className="flex flex-col gap-1">
                              <label className="flex items-center gap-1 text-[10px] cursor-pointer" style={{ color: 'var(--text-muted)' }}>
                                <input type="checkbox" checked={!!editForm.can_manage_users}
                                  onChange={e => setEditForm(p => ({ ...p, can_manage_users: e.target.checked }))}
                                  className="h-3 w-3 rounded accent-steel-blue dark:accent-gold" />
                                {t('users.can_manage')}
                              </label>
                              <label className="flex items-center gap-1 text-[10px] cursor-pointer" style={{ color: 'var(--text-muted)' }}>
                                <input type="checkbox" checked={!!editForm.can_create_events}
                                  onChange={e => setEditForm(p => ({ ...p, can_create_events: e.target.checked }))}
                                  className="h-3 w-3 rounded accent-steel-blue dark:accent-gold" />
                                {t('users.can_create_events')}
                              </label>
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-2 text-right">
                          <button onClick={() => handleUpdate(u.id)}
                            className="text-xs font-semibold mr-2 hover:underline"
                            style={{ color: 'var(--io-accent)' }}>
                            {t('common.save')}
                          </button>
                          <button onClick={() => setEditingId(null)}
                            className="text-xs hover:underline"
                            style={{ color: 'var(--text-subtle)' }}>
                            {t('common.cancel')}
                          </button>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="px-4 py-2 font-medium" style={{ color: 'var(--text-primary)' }}>
                          {u.full_name}
                          {u.id === currentUser?.id && (
                            <span className="ml-1 text-[9px]" style={{ color: 'var(--text-subtle)' }}>
                              {t('common.you')}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-2 text-xs" style={{ color: 'var(--text-muted)' }}>{u.email}</td>
                        <td className="px-4 py-2">
                          {(() => {
                            // v0.50j: only super_admin and staff exist as
                            // system roles now. The old event_admin pill
                            // tuple is gone.
                            const roleStyle =
                              u.role === 'super_admin' ? { bg: 'rgba(128,0,32,0.12)', color: 'var(--alert-burgundy)' } :
                              { bg: 'rgba(128,128,128,0.12)', color: 'var(--text-muted)' };
                            return (
                              <span className="text-xs font-semibold px-1.5 py-0.5 rounded"
                                style={{ background: roleStyle.bg, color: roleStyle.color }}>
                                {t('role.' + u.role)}
                              </span>
                            );
                          })()}
                          {/* v0.50j: capability badges shown inline with
                              the role pill for any Staff user with flags
                              granted. Super Admin has both implicitly and
                              doesn't need the clutter. */}
                          {u.role !== 'super_admin' && u.can_manage_users && (
                            <span className="ml-1 text-[9px]" style={{ color: 'var(--text-subtle)' }}>
                              + user mgmt
                            </span>
                          )}
                          {u.role !== 'super_admin' && u.can_create_events && (
                            <span className="ml-1 text-[9px]" style={{ color: 'var(--text-subtle)' }}>
                              + events
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-2">
                          <span className="text-xs font-semibold"
                            style={{ color: u.is_active ? 'var(--io-accent)' : 'var(--pending-color)' }}>
                            {u.is_active ? t('common.active') : t('common.inactive')}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-right">
                          <div className="flex items-center justify-end gap-3">
                            {u.id !== currentUser?.id && (
                              <>
                                <button onClick={() => startEdit(u)}
                                  className="text-xs font-semibold hover:underline"
                                  style={{ color: 'var(--io-accent)' }}>
                                  {t('common.edit')}
                                </button>
                                <button onClick={() => handleDeactivate(u)}
                                  className="text-xs font-semibold hover:underline"
                                  style={{ color: u.is_active ? 'var(--alert-burgundy)' : 'var(--io-accent)' }}>
                                  {u.is_active ? t('users.deactivate') : t('users.reactivate')}
                                </button>
                              </>
                            )}
                            {u.id !== currentUser?.id && (isSuperAdmin || u.role !== 'super_admin') && (
                              <button onClick={() => handleDelete(u)}
                                className="text-xs font-semibold hover:underline"
                                style={{ color: 'var(--alert-burgundy)' }}>
                                {t('users.delete')}
                              </button>
                            )}
                          </div>
                        </td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Danger zone note */}
      <p className="text-[10px] mt-3 text-center" style={{ color: 'var(--text-subtle)' }}>
        {t('users.danger')}
      </p>

      <ConfirmOverlay />
    </div>
  );
}
