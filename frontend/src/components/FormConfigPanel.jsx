import { useState, useEffect } from 'react';
import { events as eventsApi, customFields as cfApi } from '../services/api';
import { useConfirmOverlay } from './ConfirmOverlay';
import { useI18n } from '../hooks/useI18n';
import { useToast } from '../hooks/useToast';

import TranslatedError from './TranslatedError';
export default function FormConfigPanel({ eventId, isAdmin }) {
  const [fields, setFields] = useState([]);
  const [customFieldList, setCustomFieldList] = useState([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);
  const [showAddCustom, setShowAddCustom] = useState(false);
  const [newField, setNewField] = useState({ label: '', field_type: 'text', is_required: false, options: '', show_in_form: true });
  const [editingFieldId, setEditingFieldId] = useState(null);
  const [editField, setEditField] = useState({ label: '', field_type: 'text', is_required: false, options: '', show_in_form: true });
  const [loading, setLoading] = useState(true);
  const { confirm, ConfirmOverlay } = useConfirmOverlay();
  const { t } = useI18n();
  const { showToast, ToastHost } = useToast();

  const FIELD_LABELS = {
    gender: t('register.gender'),
    date_of_birth: t('register.dob'),
    phone: t('register.phone'),
    address: t('register.address'),
    country: t('register.country'),
    church_organisation: t('register.church'),
  };

  const FIELD_TYPES = [
    { value: 'text', label: t('event.field.type.text') },
    { value: 'number', label: t('event.field.type.number') },
    { value: 'select', label: t('event.field.type.select') },
    { value: 'boolean', label: t('event.field.type.boolean') },
    { value: 'date', label: t('event.field.type.date') },
  ];

  useEffect(() => { loadAll(); }, [eventId]);

  const loadAll = async () => {
    try {
      const [fieldsData, customData] = await Promise.all([eventsApi.getFields(eventId), cfApi.list(eventId)]);
      setFields(fieldsData); setCustomFieldList(customData);
    } catch (err) { setError(err); }
    finally { setLoading(false); }
  };

  // v50b-7: auto-save on every toggle. No more explicit "Save field settings"
  // button. We debounce by 300ms so rapid sequential toggles batch into one
  // PATCH, keeping the server quiet.
  // v0.70d-3a-4 (M1): toast fires once per debounced commit, not per
  // toggle — so rapid clicking through field visibility settings
  // produces ONE toast at the end of the burst, not N spammy ones.
  const persistFields = async (nextFields) => {
    setSaving(true); setError(null);
    try {
      await eventsApi.setFields(
        eventId,
        nextFields.map(f => ({ field_name: f.field_name, is_enabled: f.is_enabled, is_required: f.is_required }))
      );
      setSaved(true);
      showToast(t('form.fields_updated'), 'success');
      setTimeout(() => setSaved(false), 1200);
    } catch (err) { setError(err); }
    finally { setSaving(false); }
  };

  // Debounce timer ref so multiple toggles within 300ms only fire one PATCH.
  const saveTimerRef = useState({ current: null })[0];
  const scheduleSave = (nextFields) => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => persistFields(nextFields), 300);
  };

  const toggleField = (fieldName, key) => {
    setFields(prev => {
      const next = prev.map(f => f.field_name === fieldName ? { ...f, [key]: !f[key] } : f);
      scheduleSave(next);
      return next;
    });
  };

  // Legacy: still used by the "Save now" affordance if we ever need one;
  // currently unreferenced by the UI after the auto-save refactor.
  // Prefixed with _ to match ESLint's ignore pattern while kept for reference.
  const _handleSaveFields = async () => {
    if (saveTimerRef.current) { clearTimeout(saveTimerRef.current); saveTimerRef.current = null; }
    await persistFields(fields);
  };

  const handleAddCustom = async (e) => {
    e.preventDefault();
    if (!newField.label.trim()) return;
    try {
      const payload = { label: newField.label.trim(), field_type: newField.field_type, is_required: newField.is_required, show_in_form: newField.show_in_form };
      if (newField.field_type === 'select' && newField.options.trim()) {
        payload.options = newField.options.split(',').map(o => o.trim()).filter(Boolean);
      }
      await cfApi.create(eventId, payload);
      setNewField({ label: '', field_type: 'text', is_required: false, options: '', show_in_form: true });
      setShowAddCustom(false);
      await loadAll();
    } catch (err) { setError(err); }
  };

  const handleDeleteCustom = async (fieldId) => {
    const ok = await confirm({ title: t('event.field.delete.title'), message: t('event.field.delete.message'), confirmLabel: t('event.field.delete.confirm'), danger: true });
    if (!ok) return;
    try { await cfApi.delete(eventId, fieldId); await loadAll(); }
    catch (err) { setError(err); }
  };

  const handleEditCustom = (cf) => {
    setEditingFieldId(cf.id);
    setEditField({
      label: cf.label,
      field_type: cf.field_type,
      is_required: cf.is_required || false,
      show_in_form: cf.show_in_form !== false,  // default true if undefined (legacy)
      options: cf.options?.choices ? cf.options.choices.join(', ') : '',
    });
  };

  const handleUpdateCustom = async (e) => {
    e.preventDefault();
    if (!editField.label.trim()) return;
    try {
      const payload = { label: editField.label.trim(), field_type: editField.field_type, is_required: editField.is_required, show_in_form: editField.show_in_form };
      if (editField.field_type === 'select' && editField.options.trim()) {
        payload.options = editField.options.split(',').map(o => o.trim()).filter(Boolean);
      }
      await cfApi.update(eventId, editingFieldId, payload);
      setEditingFieldId(null);
      await loadAll();
    } catch (err) { setError(err); }
  };

  if (loading) return <p className="text-sm" style={{ color: 'var(--text-subtle)' }}>{t('common.loading')}</p>;

  // v0.50d-5d: shared input style for this panel's inline forms — CSS
  // var backgrounds/borders, theme-aware focus ring.
  const inputClass =
    "w-full rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]";

  return (
    <div>
      <h3 className="font-heading font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
        {t('event.form_fields')}
      </h3>
      <p className="text-xs mb-4" style={{ color: 'var(--text-subtle)' }}>
        {t('event.form_fields.hint')}
      </p>

      <TranslatedError err={error} />

      {/* ─── Built-in fields ─── */}
      <div
        className="card-surface-solid rounded-2xl overflow-hidden mb-4"
        style={{ border: '1px solid var(--card-border)' }}
      >
        <div
          className="px-4 py-2"
          style={{ background: 'rgba(0,0,0,0.02)', borderBottom: '1px solid var(--card-border)' }}
        >
          <span className="text-[10px] uppercase tracking-caps font-semibold" style={{ color: 'var(--text-subtle)' }}>
            {t('event.builtin_fields')}
          </span>
        </div>
        <div>
          {fields.map((f, i) => (
            <div key={f.field_name}
              className="flex items-center justify-between px-4 py-2.5"
              style={i > 0 ? { borderTop: '1px solid var(--card-border)' } : undefined}>
              <span className="text-sm" style={{ color: 'var(--text-primary)' }}>
                {FIELD_LABELS[f.field_name] || f.field_name}
              </span>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-1.5 text-xs cursor-pointer" style={{ color: 'var(--text-muted)' }}>
                  <input type="checkbox" checked={f.is_enabled} onChange={() => toggleField(f.field_name, 'is_enabled')} disabled={!isAdmin}
                    className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold" />
                  {t('event.field.show')}
                </label>
                <label className="flex items-center gap-1.5 text-xs cursor-pointer" style={{ color: 'var(--text-muted)' }}>
                  <input type="checkbox" checked={f.is_required} onChange={() => toggleField(f.field_name, 'is_required')} disabled={!isAdmin || !f.is_enabled}
                    className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold" />
                  {t('event.field.required')}
                </label>
              </div>
            </div>
          ))}
        </div>
      </div>

      {isAdmin && (
        <div className="flex items-center gap-2 mb-6 text-xs" style={{ color: 'var(--text-subtle)' }}>
          {saving && <span>{t('common.saving')}</span>}
          {saved && !saving && (
            <span style={{ color: 'var(--io-accent)' }}>✓ {t('common.saved')}</span>
          )}
        </div>
      )}

      {/* ─── Custom fields ─── */}
      <div
        className="card-surface-solid rounded-2xl overflow-hidden mb-4"
        style={{ border: '1px solid var(--card-border)' }}
      >
        <div
          className="px-4 py-2 flex items-center justify-between"
          style={{ background: 'rgba(0,0,0,0.02)', borderBottom: '1px solid var(--card-border)' }}
        >
          <span className="text-[10px] uppercase tracking-caps font-semibold" style={{ color: 'var(--text-subtle)' }}>
            {t('event.custom_fields')} ({customFieldList.length})
          </span>
          {isAdmin && (
            <button onClick={() => setShowAddCustom(!showAddCustom)}
              className="text-xs font-semibold hover:underline"
              style={{ color: 'var(--io-accent)' }}>
              {showAddCustom ? t('common.cancel') : t('event.field.add')}
            </button>
          )}
        </div>

        {showAddCustom && (
          <form onSubmit={handleAddCustom}
            className="p-4 space-y-2"
            style={{ borderBottom: '1px solid var(--card-border)' }}>
            <input type="text" placeholder={`${t('event.field.label')} *`} value={newField.label}
              onChange={(e) => setNewField(p => ({ ...p, label: e.target.value }))} required
              className={inputClass} />
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[10px] uppercase tracking-caps font-semibold mb-0.5"
                  style={{ color: 'var(--text-subtle)' }}>
                  {t('event.field.type')}
                </label>
                <select value={newField.field_type}
                  onChange={(e) => setNewField(p => ({ ...p, field_type: e.target.value }))}
                  className={inputClass}>
                  {FIELD_TYPES.map(ft => <option key={ft.value} value={ft.value}>{ft.label}</option>)}
                </select>
              </div>
              <div className="flex items-end">
                <label className="flex items-center gap-1.5 text-xs cursor-pointer pb-1.5"
                  style={{ color: 'var(--text-muted)' }}>
                  <input type="checkbox" checked={newField.is_required}
                    onChange={(e) => setNewField(p => ({ ...p, is_required: e.target.checked }))}
                    className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold" />
                  {t('event.field.required')}
                </label>
              </div>
            </div>
            {newField.field_type === 'select' && (
              <input type="text" placeholder={t('event.field.options')} value={newField.options}
                onChange={(e) => setNewField(p => ({ ...p, options: e.target.value }))}
                className={inputClass} />
            )}
            <label className="flex items-center gap-1.5 text-xs cursor-pointer"
              style={{ color: 'var(--text-muted)' }}>
              <input type="checkbox" checked={newField.show_in_form}
                onChange={(e) => setNewField(p => ({ ...p, show_in_form: e.target.checked }))}
                className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold" />
              {t('event.field.show_in_form')}
            </label>
            <button type="submit"
              className="text-xs font-semibold px-3 py-1.5 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80 transition-colors">
              {t('event.field.add_submit')}
            </button>
          </form>
        )}

        {customFieldList.length === 0 && !showAddCustom ? (
          <div className="p-4 text-center text-xs" style={{ color: 'var(--text-subtle)' }}>
            {t('event.field.no_custom')}
          </div>
        ) : (
          <div>
            {customFieldList.map((cf, i) => (
              <div key={cf.id} style={i > 0 ? { borderTop: '1px solid var(--card-border)' } : undefined}>
                {editingFieldId === cf.id ? (
                  <form onSubmit={handleUpdateCustom}
                    className="p-4 space-y-2"
                    style={{
                      borderLeft: '3px solid var(--io-accent)',
                      background: 'rgba(70,130,180,0.04)',
                    }}>
                    <input type="text" value={editField.label}
                      onChange={e => setEditField(p => ({ ...p, label: e.target.value }))} required
                      className={inputClass} />
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-[10px] uppercase tracking-caps font-semibold mb-0.5"
                          style={{ color: 'var(--text-subtle)' }}>
                          {t('event.field.type')}
                        </label>
                        <select value={editField.field_type}
                          onChange={e => setEditField(p => ({ ...p, field_type: e.target.value }))}
                          className={inputClass}>
                          {FIELD_TYPES.map(ft => <option key={ft.value} value={ft.value}>{ft.label}</option>)}
                        </select>
                      </div>
                      <div className="flex items-end">
                        <label className="flex items-center gap-1.5 text-xs cursor-pointer pb-1.5"
                          style={{ color: 'var(--text-muted)' }}>
                          <input type="checkbox" checked={editField.is_required}
                            onChange={e => setEditField(p => ({ ...p, is_required: e.target.checked }))}
                            className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold" />
                          {t('event.field.required')}
                        </label>
                      </div>
                    </div>
                    {editField.field_type === 'select' && (
                      <input type="text" placeholder={t('event.field.options')} value={editField.options}
                        onChange={e => setEditField(p => ({ ...p, options: e.target.value }))}
                        className={inputClass} />
                    )}
                    {/* v0.86 #16: show_in_form toggle. Default true for fields
                        created via this panel; false for fields auto-created
                        by CSV import. Admins can flip it either way here. */}
                    <label className="flex items-center gap-1.5 text-xs cursor-pointer"
                      style={{ color: 'var(--text-muted)' }}>
                      <input type="checkbox" checked={editField.show_in_form}
                        onChange={e => setEditField(p => ({ ...p, show_in_form: e.target.checked }))}
                        className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold" />
                      {t('event.field.show_in_form')}
                    </label>
                    <div className="flex items-center gap-2">
                      <button type="submit"
                        className="text-xs font-semibold px-3 py-1.5 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80">
                        {t('common.save')}
                      </button>
                      <button type="button" onClick={() => setEditingFieldId(null)}
                        className="text-xs hover:underline px-2"
                        style={{ color: 'var(--text-subtle)' }}>
                        {t('common.cancel')}
                      </button>
                    </div>
                  </form>
                ) : (
                  <div className="flex items-center justify-between px-4 py-2.5 gap-3">
                    <div className="min-w-0">
                      <span className="text-sm" style={{ color: 'var(--text-primary)' }}>{cf.label}</span>
                      <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded"
                        style={{
                          color: 'var(--text-subtle)',
                          background: 'rgba(0,0,0,0.05)',
                        }}>
                        {cf.field_type}
                      </span>
                      {cf.is_required && (
                        <span className="ml-1 text-[10px]" style={{ color: 'var(--alert-burgundy)' }}>
                          {t('common.required')}
                        </span>
                      )}
                      {/* v0.86 #16: badge for fields that are NOT on the
                          public registration form. Created by CSV import
                          (auto, default off) or manually toggled off. */}
                      {cf.show_in_form === false && (
                        <span className="ml-1 text-[10px] px-1.5 py-0.5 rounded"
                          style={{
                            color: 'var(--text-subtle)',
                            background: 'rgba(212,168,44,0.15)',
                          }}>
                          {t('event.field.hidden_from_form')}
                        </span>
                      )}
                      {cf.options?.choices && (
                        <span className="ml-2 text-[10px]" style={{ color: 'var(--text-subtle)' }}>
                          {cf.options.choices.join(', ')}
                        </span>
                      )}
                    </div>
                    {isAdmin && (
                      <div className="flex gap-3 shrink-0">
                        <button onClick={() => handleEditCustom(cf)}
                          className="text-xs font-semibold hover:underline"
                          style={{ color: 'var(--io-accent)' }}>
                          {t('common.edit')}
                        </button>
                        <button onClick={() => handleDeleteCustom(cf.id)}
                          className="text-xs font-semibold hover:underline"
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
      </div>
      <ConfirmOverlay />
      <ToastHost />
    </div>
  );
}
