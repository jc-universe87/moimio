import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { participants } from '../services/api';
import { I18nProvider, useI18n, SUPPORTED_LANGS } from '../hooks/useI18n';
import TranslatedError from '../components/TranslatedError';

// Inner component — uses i18n context
function RegisterForm() {
  const { eventId } = useParams();
  const [event, setEvent] = useState(null);
  const [fields, setFields] = useState([]);
  const [customFields, setCustomFields] = useState([]);
  const [formData, setFormData] = useState({
    first_name: '', last_name: '', email: '',
    gender: '', date_of_birth: '', phone: '',
    address: '', country: '', church_organisation: '',
    message: '', group_code: '', group_code_categories: null, gdpr_consent: false,
  });
  const [customValues, setCustomValues] = useState({});
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [confirmationRequired, setConfirmationRequired] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [prefEnabled, setPrefEnabled] = useState(false);
  const [categories, setCategories] = useState([]);
  const [preferences, setPreferences] = useState([
    { preferred_participant_number: '', preferred_name: '', preferred_details: '', category_scope: 'all' }
  ]);
  // Grouping mode: 'none' (default) | 'code' (have a group code) | 'request' (have name only)
  const [groupingMode, setGroupingMode] = useState('none');
  const [extraPersons, setExtraPersons] = useState([]); // multi-person registration
  // v0.70d-3c-8a: per-extra-person validation errors. Same shape as
  // extraPersons but values are error-flag objects:
  // { first_name?: bool, last_name?: bool, email?: bool, gender?: bool,
  //   date_of_birth?: bool, gdpr_consent?: bool }
  // Pre-flight populated in handleSubmit before any backend call.
  const [extraPersonErrors, setExtraPersonErrors] = useState([]);
  const [collapsedPersons, setCollapsedPersons] = useState(new Set()); // collapsed extra person indices
  const draftKey = eventId ? `moimio_reg_draft_${eventId}` : null;

  const { t, lang, setLang, setLangOverride } = useI18n();

  useEffect(() => { loadEvent(); }, [eventId]);

  const loadEvent = async () => {
    try {
      const res = await fetch(`/api/events/${eventId}/public`);
      if (!res.ok) throw new Error('Event not found');
      const eventData = await res.json();
      setEvent(eventData);
      setConfirmationRequired(eventData.settings?.require_email_confirmation || false);
      // Apply event's default language if user hasn't overridden
      const defaultLang = eventData.settings?.default_language;
      if (defaultLang && !sessionStorage.getItem('moimio_lang_override')) {
        setLang(defaultLang);
      }
      const fieldsRes = await fetch(`/api/events/${eventId}/fields/public`);
      if (fieldsRes.ok) setFields(await fieldsRes.json());
      const cfRes = await fetch(`/api/events/${eventId}/custom-fields/public`);
      if (cfRes.ok) setCustomFields(await cfRes.json());
      // Load categories for preference scope selector (if prefs enabled)
      if (eventData.settings?.enable_group_preferences) {
        setPrefEnabled(true);
        const catRes = await fetch(`/api/events/${eventId}/allocation-categories/public`);
        if (catRes.ok) setCategories(await catRes.json());
      }
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
      // Restore draft if present
      if (draftKey) {
        try {
          const draft = localStorage.getItem(draftKey);
          if (draft) {
            const d = JSON.parse(draft);
            if (d.formData) setFormData(fd => ({ ...fd, ...d.formData }));
            if (d.customValues) setCustomValues(d.customValues);
            if (d.extraPersons) setExtraPersons(d.extraPersons);
            if (d.groupingMode) setGroupingMode(d.groupingMode);
          }
        } catch {}
      }
    }
  };

  // Save draft on every change
  const saveDraft = (patch) => {
    if (!draftKey) return;
    try {
      const current = (() => { try { return JSON.parse(localStorage.getItem(draftKey) || '{}'); } catch { return {}; } })();
      localStorage.setItem(draftKey, JSON.stringify({ ...current, ...patch }));
    } catch {}
  };

  const clearDraft = () => { if (draftKey) { try { localStorage.removeItem(draftKey); } catch {} } };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    const updated = { ...formData, [name]: type === 'checkbox' ? checked : value };
    setFormData(updated);
    saveDraft({ formData: updated });
  };

  const handleCustomChange = (fieldId, value) => {
    setCustomValues(prev => ({ ...prev, [fieldId]: value }));
  };

  const updatePref = (idx, field, value) => {
    setPreferences(prev => prev.map((p, i) => i === idx ? { ...p, [field]: value } : p));
  };
  const addPref = () => setPreferences(prev => [...prev, { preferred_participant_number: '', preferred_name: '', preferred_details: '', category_scope: 'all' }]);
  const removePref = (idx) => setPreferences(prev => prev.filter((_, i) => i !== idx));

  const isFieldEnabled = (name) => fields.find(f => f.field_name === name)?.is_enabled || false;
  const isFieldRequired = (name) => fields.find(f => f.field_name === name)?.is_required || false;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      // v0.70d-3c-9: pre-flight runs FIRST, before any submission
      // building. If extras are incomplete: scroll to first error,
      // expand collapsed cards with errors, refuse to submit.
      // 8a moved the validation in but kept it AFTER the primary
      // submission was built; this version makes it the first thing
      // so behaviour is unambiguous.
      const epErrors = extraPersons.map((ep) => {
        const errs = {};
        if (!ep.first_name?.trim()) errs.first_name = true;
        if (!ep.last_name?.trim()) errs.last_name = true;
        if (!ep.email?.trim()) errs.email = true;
        if (!ep.gdpr_consent) errs.gdpr_consent = true;
        if (isFieldEnabled('gender') && isFieldRequired('gender') && !ep.gender) errs.gender = true;
        if (isFieldEnabled('date_of_birth') && isFieldRequired('date_of_birth') && !ep.date_of_birth) errs.date_of_birth = true;
        // v1.0.0k #6: extend required-field check to phone, address,
        // country, church_organisation. Previously only name, email,
        // gdpr, gender, DOB were validated for extras — if the
        // organiser had marked phone required, the extras would
        // silently submit empty.
        if (isFieldEnabled('phone') && isFieldRequired('phone') && !ep.phone?.trim()) errs.phone = true;
        if (isFieldEnabled('address') && isFieldRequired('address') && !ep.address?.trim()) errs.address = true;
        if (isFieldEnabled('country') && isFieldRequired('country') && !ep.country?.trim()) errs.country = true;
        if (isFieldEnabled('church_organisation') && isFieldRequired('church_organisation') && !ep.church_organisation?.trim()) errs.church_organisation = true;
        // v1.0.0k #5: required custom fields validated per-person.
        // Errors keyed as `cf_${cf.id}` so they don't collide with
        // built-in field names. epInputClass + epCustomFieldClass
        // pick the same prefix.
        for (const cf of customFields) {
          if (cf.is_required) {
            const v = ep.customValues?.[cf.id];
            // Boolean fields are "filled" if set to either 'true' or
            // 'false'. Other types: any non-empty string.
            if (cf.field_type === 'boolean') {
              if (v !== 'true' && v !== 'false') errs[`cf_${cf.id}`] = true;
            } else {
              if (!v || !String(v).trim()) errs[`cf_${cf.id}`] = true;
            }
          }
        }
        return errs;
      });
      const firstErrorIdx = epErrors.findIndex(e => Object.keys(e).length > 0);
      if (firstErrorIdx >= 0) {
        setExtraPersonErrors(epErrors);
        const incompleteCount = epErrors.filter(e => Object.keys(e).length > 0).length;
        setError({ i18nKey: 'errors.register.extra_people_incomplete', i18nParams: { count: incompleteCount } });
        // Auto-expand any collapsed extra-person card that has errors
        // so the user can see the highlighted fields.
        setCollapsedPersons(prev => {
          const next = new Set(prev);
          epErrors.forEach((errs, i) => {
            if (Object.keys(errs).length > 0) next.delete(i);
          });
          return next;
        });
        setSubmitting(false);
        // Scroll to first errored extra-person card after a tick so React
        // has rendered the highlight + expansion change.
        setTimeout(() => {
          const el = document.getElementById(`extra-person-${firstErrorIdx}`);
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
          } else {
            // Fallback: scroll to the page-level error banner at top of form
            const errEl = document.getElementById('register-error-banner');
            if (errEl) errEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        }, 50);
        return;
      }
      // All extras valid — proceed to building primary submission.
      const submission = {
        first_name: formData.first_name, last_name: formData.last_name,
        email: formData.email, gdpr_consent: formData.gdpr_consent,
      };
      const optFields = ['gender', 'date_of_birth', 'phone', 'address', 'country', 'church_organisation'];
      for (const f of optFields) {
        if (isFieldEnabled(f) && formData[f]) submission[f] = formData[f];
      }
      if (formData.message) submission.message = formData.message;
      // Send group_code only if user picked 'code' mode
      if (groupingMode === 'code' && formData.group_code.trim()) {
        submission.group_code = formData.group_code.trim();
        if (formData.group_code_categories) submission.group_code_categories = formData.group_code_categories;
      }
      const cfEntries = Object.entries(customValues).filter(([_, v]) => v);
      if (cfEntries.length > 0) submission.custom_fields = Object.fromEntries(cfEntries);
      submission.preferred_language = lang;
      // Send preference requests only if user picked 'request' mode and prefs are enabled
      if (groupingMode === 'request' && prefEnabled) {
        const filledPrefs = preferences.filter(p => p.preferred_name.trim() || p.preferred_participant_number);
        if (filledPrefs.length > 0) {
          submission.preference_requests = filledPrefs.map(p => ({
            preferred_participant_number: p.preferred_participant_number ? parseInt(p.preferred_participant_number) : null,
            preferred_name: p.preferred_name.trim() || null,
            preferred_details: p.preferred_details.trim() || null,
            category_scope: p.category_scope,
          }));
        }
      }
      await participants.register(eventId, submission);

      // All extras pre-validated above — just submit, no skip-on-empty.
      for (const ep of extraPersons) {
        const epSubmission = {
          first_name: ep.first_name.trim(),
          last_name: ep.last_name.trim(),
          email: ep.email.trim(),
          gdpr_consent: ep.gdpr_consent,
          preferred_language: lang,
        };
        if (ep.date_of_birth) epSubmission.date_of_birth = ep.date_of_birth;
        if (ep.message) epSubmission.message = ep.message;
        // Copy shared fields from primary if toggle on. v0.55.1: gender is
        // deliberately NOT included here. Gender is a per-person attribute
        // like name/email — always taken from the individual's own field,
        // never inherited from the primary registrant, even in copy mode.
        if (ep.copyFromPrimary) {
          if (formData.phone) epSubmission.phone = formData.phone;
          if (formData.address) epSubmission.address = formData.address;
          if (formData.country) epSubmission.country = formData.country;
          if (formData.church_organisation) epSubmission.church_organisation = formData.church_organisation;
        } else {
          if (ep.phone) epSubmission.phone = ep.phone;
          if (ep.address) epSubmission.address = ep.address;
          if (ep.country) epSubmission.country = ep.country;
          if (ep.church_organisation) epSubmission.church_organisation = ep.church_organisation;
        }
        // Gender: always per-person, regardless of copy mode.
        if (ep.gender) epSubmission.gender = ep.gender;
        // Group code: per-person three-way choice.
        // 'own'  → use ep.group_code if filled, otherwise no code sent
        // 'none' → explicitly no code, even if primary has one
        // 'same' → inherit primary's code (or no code if primary has none)
        if (ep.groupCodeMode === 'own' && ep.group_code?.trim()) {
          epSubmission.group_code = ep.group_code.trim();
        } else if (ep.groupCodeMode === 'same') {
          if (groupingMode === 'code' && formData.group_code.trim()) {
            epSubmission.group_code = formData.group_code.trim();
            if (formData.group_code_categories) epSubmission.group_code_categories = formData.group_code_categories;
          }
        }
        // 'none' falls through: no group_code attached.
        // v1.0.0k #5: per-person custom field values. Mirrors the
        // primary's payload shape — empty values are filtered out so
        // the backend treats unset fields the same way for primary
        // and extras.
        const epCfEntries = Object.entries(ep.customValues || {}).filter(([_, v]) => v !== '' && v != null);
        if (epCfEntries.length > 0) {
          epSubmission.custom_fields = Object.fromEntries(epCfEntries);
        }
        await participants.register(eventId, epSubmission);
      }

      clearDraft();
      setSuccess(true);
    } catch (err) {
      setError(err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-off-white">
      <p className="text-gray-400">{t('common.loading')}</p>
    </div>
  );

  if (!event) return (
    <div className="min-h-screen flex items-center justify-center bg-off-white">
      <div className="text-center">
        <h1 className="font-heading text-2xl font-bold text-deep-navy mb-2">{t('register.event_not_found')}</h1>
        <p className="text-gray-500">{t('register.event_not_found.hint')}</p>
      </div>
    </div>
  );

  if (success) return (
    <div className="min-h-screen flex items-center justify-center bg-off-white p-4">
      <div className="w-full max-w-md text-center">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8">
          <div className="text-5xl mb-4" style={{ color: 'var(--io-accent)' }}>✓</div>
          <h2 className="font-heading text-2xl font-bold text-deep-navy mb-2">
            {confirmationRequired ? t('register.success.title.email') : t('register.success.title.done')}
          </h2>
          <p className="text-gray-500">
            {confirmationRequired
              ? t('register.success.email', { email: formData.email, event: event.name })
              : t('register.success.done', { event: event.name })}
          </p>
        </div>
      </div>
    </div>
  );

  // Custom style
  const es = event?.settings?.style || {};
  const cs = {
    primaryColor: es.primaryColor || '#4682B4',
    bgColor: es.bgColor || '#F7F5F2',
    textColor: es.textColor || '#0F1E2E',
    borderRadius: es.borderRadius || '12',
    fontFamily: es.fontFamily || 'Nunito Sans',
  };
  const hasCustomStyle = !!event?.settings?.style;
  const radius = `${Math.min(parseInt(cs.borderRadius), 16)}px`;
  const inputClass = "w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:border-transparent"
  // v0.70d-3c-8a: per-extra-person field error highlighting.
  // Returns inputClass with a burgundy border if the field has an
  // error in extraPersonErrors[idx]. Auto-clears as user types
  // (handled in updateEp via onChange path).
  const epInputClass = (idx, field) => {
    const hasErr = extraPersonErrors[idx]?.[field];
    if (!hasErr) return inputClass;
    return inputClass.replace('border-gray-200', 'border-burgundy ring-1 ring-burgundy/40');
  };
    + (hasCustomStyle ? '' : ' focus:ring-steel-blue');

  const OPTIONAL_FIELDS = [
    { name: 'gender', labelKey: 'register.gender', type: 'select' },
    { name: 'date_of_birth', labelKey: 'register.dob', type: 'date' },
    { name: 'phone', labelKey: 'register.phone', type: 'tel' },
    { name: 'address', labelKey: 'register.address', type: 'text' },
    { name: 'country', labelKey: 'register.country', type: 'text' },
    { name: 'church_organisation', labelKey: 'register.church', type: 'text' },
  ];

  return (
    <div className={`min-h-screen py-8 px-4 ${hasCustomStyle ? '' : 'bg-off-white'}`}
      style={hasCustomStyle ? { backgroundColor: cs.bgColor, fontFamily: `'${cs.fontFamily}', sans-serif` } : {}}>
      {hasCustomStyle && <link rel="stylesheet" href={`https://fonts.googleapis.com/css2?family=${encodeURIComponent(cs.fontFamily)}:wght@400;600;700&display=swap`} />}
      {hasCustomStyle && (
        <style>{`
          .moimio-form input:focus, .moimio-form select:focus, .moimio-form textarea:focus {
            box-shadow: 0 0 0 2px ${cs.primaryColor}40; border-color: ${cs.primaryColor};
          }
        `}</style>
      )}

      <div className="max-w-lg mx-auto">
        {/* Header with language switcher */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-3">
            <img src="/logogram.svg" alt="Moimio" className="w-10 h-10" />
            {/* Wordmark: organiser-customised path uses their palette;
                brand fallback matches §9.3 (Steel Blue io on light bg). */}
            <h1 className="font-heading leading-none"
                style={{ fontSize: '20px', fontWeight: 800, letterSpacing: '0.068em' }}>
              <span style={hasCustomStyle ? { color: cs.textColor } : { color: '#0F1E2E' }}>MOIM</span>
              <span style={hasCustomStyle
                      ? { color: cs.primaryColor, fontSize: '12.7px', fontWeight: 700, letterSpacing: '0.045em', position: 'relative', top: '-0.05em' }
                      : { color: '#4682B4', fontSize: '12.7px', fontWeight: 700, letterSpacing: '0.045em', position: 'relative', top: '-0.05em' }}>io</span>
            </h1>
          </div>

        </div>

        <div className="bg-white shadow-sm border border-gray-100 p-6" style={{ borderRadius: radius }}>
          {/* Event info */}
          <div className="mb-6">
            <h2 className="font-heading text-xl font-bold" style={hasCustomStyle ? { color: cs.textColor } : {}}>{event.name}</h2>
            {event.description && <p className="text-gray-500 text-sm mt-1">{event.description}</p>}
            {event.location && <p className="text-gray-400 text-sm mt-1">{event.location}</p>}
            {event.start_date && (
              <p className="text-gray-400 text-sm">
                {new Date(event.start_date + 'T00:00:00').toLocaleDateString()}
                {event.end_date ? ` – ${new Date(event.end_date + 'T00:00:00').toLocaleDateString()}` : ''}
              </p>
            )}
          </div>

          <div id="register-error-banner"><TranslatedError err={error} className="text-sm rounded-lg p-3 mb-4" /></div>

          <form id="register-form" onSubmit={handleSubmit} className="moimio-form space-y-4">
            {/* Required: name + email */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-600 mb-1">
                  {t('register.first_name')} <span style={{ color: 'var(--alert-burgundy)' }}>*</span>
                </label>
                <input type="text" name="first_name" value={formData.first_name} onChange={handleChange} required className={inputClass} />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-600 mb-1">
                  {t('register.last_name')} <span style={{ color: 'var(--alert-burgundy)' }}>*</span>
                </label>
                <input type="text" name="last_name" value={formData.last_name} onChange={handleChange} required className={inputClass} />
              </div>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-600 mb-1">
                {t('register.email')} <span style={{ color: 'var(--alert-burgundy)' }}>*</span>
              </label>
              <input type="email" name="email" value={formData.email} onChange={handleChange} required className={inputClass} />
            </div>

            {/* Optional built-in fields */}
            {OPTIONAL_FIELDS.map(({ name, labelKey, type }) => {
              if (!isFieldEnabled(name)) return null;
              const required = isFieldRequired(name);
              if (name === 'gender') return (
                <div key={name}>
                  <label className="block text-sm font-semibold text-gray-600 mb-1">
                    {t(labelKey)} {required && <span style={{ color: 'var(--alert-burgundy)' }}>*</span>}
                  </label>
                  <select name={name} value={formData[name]} onChange={handleChange} required={required} className={inputClass}>
                    <option value="">{t('register.gender.select')}</option>
                    <option value="male">{t('register.gender.male')}</option>
                    <option value="female">{t('register.gender.female')}</option>
                  </select>
                </div>
              );
              return (
                <div key={name}>
                  <label className="block text-sm font-semibold text-gray-600 mb-1">
                    {t(labelKey)} {required && <span style={{ color: 'var(--alert-burgundy)' }}>*</span>}
                  </label>
                  <input type={type} name={name} value={formData[name]} onChange={handleChange} required={required} className={inputClass} />
                </div>
              );
            })}

            {/* Custom EAV fields */}
            {customFields.map(cf => (
              <div key={cf.id}>
                <label className="block text-sm font-semibold text-gray-600 mb-1">
                  {cf.label} {cf.is_required && <span style={{ color: 'var(--alert-burgundy)' }}>*</span>}
                </label>
                {cf.field_type === 'select' && cf.options?.choices ? (
                  <select value={customValues[cf.id] || ''} onChange={e => handleCustomChange(cf.id, e.target.value)}
                    required={cf.is_required} className={inputClass}>
                    <option value="">{t('common.select')}</option>
                    {cf.options.choices.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                  </select>
                ) : cf.field_type === 'boolean' ? (
                  <label className="flex items-center gap-2 text-sm text-gray-600">
                    <input type="checkbox" checked={customValues[cf.id] === 'true'}
                      onChange={e => handleCustomChange(cf.id, e.target.checked ? 'true' : 'false')}
                      className="h-4 w-4 text-steel-blue border-gray-300 rounded focus:ring-steel-blue" />
                    {t('common.yes')}
                  </label>
                ) : (
                  <input type={cf.field_type === 'number' ? 'number' : cf.field_type === 'date' ? 'date' : 'text'}
                    value={customValues[cf.id] || ''} onChange={e => handleCustomChange(cf.id, e.target.value)}
                    required={cf.is_required} className={inputClass} />
                )}
              </div>
            ))}

            {/* ═══ UNIFIED GROUPING SECTION ═══ */}
            <div className="border border-steel-blue/20 rounded-xl p-4 bg-steel-blue/5">
              <h3 className="font-heading font-bold text-deep-navy text-sm mb-1">{t('grouping.section_title')}</h3>
              <p className="text-xs text-gray-500 mb-3 leading-relaxed">{t('grouping.section_hint')}</p>

              {/* Radio options */}
              <div className="space-y-1.5 mb-3">
                <label className="flex items-start gap-2.5 cursor-pointer p-2 rounded-lg hover:bg-white/60 transition-colors">
                  <input type="radio" name="grouping_mode" value="none"
                    checked={groupingMode === 'none'}
                    onChange={() => setGroupingMode('none')}
                    className="mt-0.5 h-4 w-4 text-steel-blue focus:ring-steel-blue" />
                  <span className="text-xs text-gray-700">{t('grouping.option_none')}</span>
                </label>

                <label className="flex items-start gap-2.5 cursor-pointer p-2 rounded-lg hover:bg-white/60 transition-colors">
                  <input type="radio" name="grouping_mode" value="code"
                    checked={groupingMode === 'code'}
                    onChange={() => setGroupingMode('code')}
                    className="mt-0.5 h-4 w-4 text-steel-blue focus:ring-steel-blue" />
                  <span className="text-xs text-gray-700">{t('grouping.option_code')}</span>
                </label>

                {prefEnabled && (
                  <label className="flex items-start gap-2.5 cursor-pointer p-2 rounded-lg hover:bg-white/60 transition-colors">
                    <input type="radio" name="grouping_mode" value="request"
                      checked={groupingMode === 'request'}
                      onChange={() => setGroupingMode('request')}
                      className="mt-0.5 h-4 w-4 text-steel-blue focus:ring-steel-blue" />
                    <span className="text-xs text-gray-700">{t('grouping.option_request')}</span>
                  </label>
                )}
              </div>

              {/* Conditional content: code mode */}
              {groupingMode === 'code' && (
                <div className="bg-white rounded-lg p-3 space-y-2">
                  <p className="text-[11px] text-gray-500 leading-relaxed">{t('grouping.code_explainer')}</p>
                  {/* Family / multi-person hint */}
                  {extraPersons.length > 0 && (
                    <div className="bg-neutral-tint rounded-lg px-3 py-2 text-[11px] leading-relaxed" style={{ color: 'var(--text-muted)', border: '1px solid var(--card-border)' }}>
                      <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>👨‍👩‍👧 {t('grouping.family_hint_title')}</span>
                      <span className="block mt-0.5">{t('grouping.family_hint_body')}</span>
                    </div>
                  )}
                  <input type="text" name="group_code" value={formData.group_code} onChange={handleChange}
                    placeholder={t('register.group_code.placeholder')}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-steel-blue" />
                </div>
              )}

              {/* Conditional content: request mode */}
              {groupingMode === 'request' && prefEnabled && (
                <div className="bg-white rounded-lg p-3 space-y-3">
                  <p className="text-[11px] text-gray-500 leading-relaxed">{t('grouping.request_explainer')}</p>
                  {preferences.map((pref, idx) => (
                    <div key={idx} className="space-y-2">
                      {idx > 0 && (
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-semibold text-gray-500">#{idx + 1}</span>
                          <button type="button" onClick={() => removePref(idx)}
                            className="text-[10px] text-alert hover:opacity-80">{t('common.remove')}</button>
                        </div>
                      )}
                      <input type="text" value={pref.preferred_name}
                        onChange={e => updatePref(idx, 'preferred_name', e.target.value)}
                        placeholder={t('grouping.request_name')}
                        className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-steel-blue" />
                      <textarea value={pref.preferred_details}
                        onChange={e => updatePref(idx, 'preferred_details', e.target.value)}
                        placeholder={t('grouping.request_details')}
                        rows={2}
                        className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-steel-blue resize-none" />
                      {/* Scoping selector ("Apply to: All / Specific group types")
                          intentionally not rendered. The category_scope field is
                          always sent as 'all' (its initial value); the backend
                          does not enforce per-category scoping in v1.0. */}
                    </div>
                  ))}
                  <button type="button" onClick={addPref}
                    className="text-[11px] text-steel-blue hover:text-mid-navy font-semibold">
                    {t('prefs.add_another')}
                  </button>
                </div>
              )}
            </div>

            {/* Message */}
            <div>
              <label className="block text-sm font-semibold text-gray-600 mb-1">{t('register.message')}</label>
              <textarea name="message" value={formData.message} onChange={handleChange} rows={3}
                placeholder={t('register.message.placeholder')}
                className={`${inputClass} resize-none`} />
            </div>

            {/* GDPR */}
            <div className="flex items-start gap-3 bg-gray-50 rounded-lg p-3">
              <input type="checkbox" name="gdpr_consent" checked={formData.gdpr_consent}
                onChange={handleChange} required
                className="mt-0.5 h-4 w-4 text-steel-blue border-gray-300 rounded focus:ring-steel-blue" />
              <label className="text-xs text-gray-600 leading-relaxed">
                {t('register.gdpr')} <span style={{ color: 'var(--alert-burgundy)' }}>*</span>
              </label>
            </div>

            <button type="submit" disabled={submitting}
              className={`w-full text-white font-semibold py-3 rounded-lg transition-colors disabled:opacity-50 text-sm ${hasCustomStyle ? '' : 'bg-steel-blue hover:bg-mid-navy'}`}
              style={hasCustomStyle ? { backgroundColor: cs.primaryColor, borderRadius: radius } : {}}>
              {submitting ? t('register.submitting') : (
                extraPersons.length > 0
                  ? t('register.submit_group').replace('{n}', extraPersons.length + 1)
                  : t('register.submit')
              )}
            </button>
          </form>

          {/* ── Multi-person: extra registrants ── */}
          {extraPersons.map((ep, idx) => {
            const isCollapsed = collapsedPersons.has(idx);
            const updateEp = (patch) => {
              const next = extraPersons.map((p, i) => i === idx ? { ...p, ...patch } : p);
              setExtraPersons(next);
              saveDraft({ extraPersons: next });
              // v0.70d-3c-8a: clear field-level errors as user fixes them.
              if (extraPersonErrors[idx]) {
                const errsCopy = [...extraPersonErrors];
                const fieldErrs = { ...errsCopy[idx] };
                Object.keys(patch).forEach((k) => {
                  if (fieldErrs[k]) delete fieldErrs[k];
                });
                // v1.0.0k #5: custom-field patches arrive under the
                // single key `customValues`. Walk the merged object
                // and clear any `cf_${id}` error whose value is now
                // filled. Without this, the burgundy border stays put
                // even after the user supplies the missing answer.
                if (patch.customValues) {
                  const merged = patch.customValues;
                  Object.keys(merged).forEach((cfId) => {
                    const v = merged[cfId];
                    const filled = (v === 'true' || v === 'false') ? true : (v && String(v).trim() !== '');
                    if (filled && fieldErrs[`cf_${cfId}`]) delete fieldErrs[`cf_${cfId}`];
                  });
                }
                errsCopy[idx] = fieldErrs;
                setExtraPersonErrors(errsCopy);
              }
            };
            return (
              <div key={idx} className="mt-4 border border-gray-200 rounded-xl overflow-hidden">
                {/* Header — always visible */}
                <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-100">
                  <button type="button"
                    onClick={() => setCollapsedPersons(s => { const n = new Set(s); n.has(idx) ? n.delete(idx) : n.add(idx); return n; })}
                    className="flex items-center gap-2 text-xs font-semibold text-deep-navy hover:text-steel-blue transition-colors">
                    <span style={{ display: 'inline-block', transform: isCollapsed ? 'none' : 'rotate(90deg)', transition: 'transform 0.15s' }}>▶</span>
                    {t('register.person_n').replace('{n}', idx + 2)}
                    {isCollapsed && ep.first_name && (
                      <span className="text-gray-500 font-normal ml-1">— {ep.first_name} {ep.last_name}</span>
                    )}
                  </button>
                  <button type="button"
                    onClick={() => {
                      setExtraPersons(ps => { const n = ps.filter((_, i) => i !== idx); saveDraft({ extraPersons: n }); return n; });
                      setExtraPersonErrors(es => es.filter((_, i) => i !== idx));
                    }}
                    className="text-xs text-alert hover:opacity-80">{t('common.remove')}</button>
                </div>

                {/* Expandable body */}
                {!isCollapsed && (
                  <div className="p-4 space-y-3">
                    {/* Copy details toggle */}
                    <label className="flex items-start gap-2 text-xs text-gray-600 cursor-pointer bg-steel-blue/5 border border-steel-blue/20 rounded-lg px-3 py-2.5">
                      <input type="checkbox" checked={ep.copyFromPrimary}
                        onChange={e => {
                          const on = e.target.checked;
                          if (on) {
                            // Immediately pre-fill from primary (except name, email,
                            // DOB, message, and GENDER — gender is always per-person
                            // per v0.55.1, same treatment as name/email).
                            updateEp({
                              copyFromPrimary: true,
                              phone: formData.phone || ep.phone,
                              address: formData.address || ep.address,
                              country: formData.country || ep.country,
                              church_organisation: formData.church_organisation || ep.church_organisation,
                            });
                          } else {
                            updateEp({ copyFromPrimary: false });
                          }
                        }}
                        className="mt-0.5 h-3.5 w-3.5 rounded shrink-0" />
                      <span>
                        <span className="font-medium">{t('register.copy_from_primary').replace('{name}', formData.first_name || t('register.primary_person'))}</span>
                        <span className="block text-gray-400 mt-0.5">{t('register.copy_from_primary.hint')}</span>
                      </span>
                    </label>

                    {/* Required: name */}
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">{t('register.first_name')} <span style={{ color: 'var(--alert-burgundy)' }}>*</span></label>
                        <input type="text" value={ep.first_name} required
                          onChange={e => updateEp({ first_name: e.target.value })}
                          className={epInputClass(idx, 'first_name')} />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">{t('register.last_name')} <span style={{ color: 'var(--alert-burgundy)' }}>*</span></label>
                        <input type="text" value={ep.last_name} required
                          onChange={e => updateEp({ last_name: e.target.value })}
                          className={epInputClass(idx, 'last_name')} />
                      </div>
                    </div>

                    {/* Email */}
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">{t('register.email')} <span style={{ color: 'var(--alert-burgundy)' }}>*</span></label>
                      <input type="email" value={ep.email} required
                        onChange={e => updateEp({ email: e.target.value })}
                        className={epInputClass(idx, 'email')} />
                    </div>

                    {/* Optional fields — same as primary form */}
                    {isFieldEnabled('gender') && (
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">{t('register.gender')}{isFieldRequired('gender') && <span className="ml-1" style={{ color: 'var(--alert-burgundy)' }}>*</span>}</label>
                        <select value={ep.gender || ''} onChange={e => updateEp({ gender: e.target.value })} className={epInputClass(idx, 'gender')}>
                          <option value="">{t('register.gender.select')}</option>
                          <option value="male">{t('register.gender.male')}</option>
                          <option value="female">{t('register.gender.female')}</option>
                        </select>
                      </div>
                    )}

                    {isFieldEnabled('date_of_birth') && (
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">{t('register.dob')}{isFieldRequired('date_of_birth') && <span className="ml-1" style={{ color: 'var(--alert-burgundy)' }}>*</span>}</label>
                        <input type="date" value={ep.date_of_birth || ''}
                          onChange={e => updateEp({ date_of_birth: e.target.value })}
                          className={epInputClass(idx, 'date_of_birth')} />
                      </div>
                    )}

                    {isFieldEnabled('phone') && (
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">{t('register.phone')}{isFieldRequired('phone') && <span className="ml-1" style={{ color: 'var(--alert-burgundy)' }}>*</span>}</label>
                        <input type="tel" value={ep.phone || ''}
                          onChange={e => updateEp({ phone: e.target.value })}
                          className={epInputClass(idx, 'phone')} />
                      </div>
                    )}

                    {isFieldEnabled('address') && (
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">{t('register.address')}{isFieldRequired('address') && <span className="ml-1" style={{ color: 'var(--alert-burgundy)' }}>*</span>}</label>
                        <input type="text" value={ep.address || ''}
                          onChange={e => updateEp({ address: e.target.value })}
                          className={epInputClass(idx, 'address')} />
                      </div>
                    )}

                    {isFieldEnabled('country') && (
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">{t('register.country')}{isFieldRequired('country') && <span className="ml-1" style={{ color: 'var(--alert-burgundy)' }}>*</span>}</label>
                        <input type="text" value={ep.country || ''}
                          onChange={e => updateEp({ country: e.target.value })}
                          className={epInputClass(idx, 'country')} />
                      </div>
                    )}

                    {isFieldEnabled('church_organisation') && (
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">{t('register.church')}{isFieldRequired('church_organisation') && <span className="ml-1" style={{ color: 'var(--alert-burgundy)' }}>*</span>}</label>
                        <input type="text" value={ep.church_organisation || ''}
                          onChange={e => updateEp({ church_organisation: e.target.value })}
                          className={epInputClass(idx, 'church_organisation')} />
                      </div>
                    )}

                    {/* v1.0.0k #5: per-extra-person custom EAV fields.
                        Mirrors the primary registrant's rendering at
                        line ~430. Values live in ep.customValues, keyed
                        by custom_field.id. Required-field highlights
                        use the `cf_${id}` key in epInputClass which
                        the validator sets alongside other errors. */}
                    {customFields.map(cf => {
                      const errKey = `cf_${cf.id}`;
                      const cfClass = epInputClass(idx, errKey);
                      const value = ep.customValues?.[cf.id] || '';
                      return (
                        <div key={cf.id}>
                          <label className="block text-xs text-gray-500 mb-1">
                            {cf.label}{cf.is_required && <span className="ml-1" style={{ color: 'var(--alert-burgundy)' }}>*</span>}
                          </label>
                          {cf.field_type === 'select' && cf.options?.choices ? (
                            <select value={value}
                              onChange={e => updateEp({ customValues: { ...(ep.customValues || {}), [cf.id]: e.target.value } })}
                              required={cf.is_required} className={cfClass}>
                              <option value="">{t('common.select')}</option>
                              {cf.options.choices.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                            </select>
                          ) : cf.field_type === 'boolean' ? (
                            <label className="flex items-center gap-2 text-xs text-gray-600">
                              <input type="checkbox" checked={value === 'true'}
                                onChange={e => updateEp({ customValues: { ...(ep.customValues || {}), [cf.id]: e.target.checked ? 'true' : 'false' } })}
                                className={extraPersonErrors[idx]?.[errKey]
                                  ? "h-4 w-4 text-steel-blue rounded border-2 border-burgundy ring-1 ring-burgundy/40"
                                  : "h-4 w-4 text-steel-blue border-gray-300 rounded"} />
                              {t('common.yes')}
                            </label>
                          ) : (
                            <input type={cf.field_type === 'number' ? 'number' : cf.field_type === 'date' ? 'date' : 'text'}
                              value={value}
                              onChange={e => updateEp({ customValues: { ...(ep.customValues || {}), [cf.id]: e.target.value } })}
                              required={cf.is_required} className={cfClass} />
                          )}
                        </div>
                      );
                    })}

                    <div>
                      <label className="block text-xs text-gray-500 mb-1">{t('register.message')}</label>
                      <textarea value={ep.message || ''} rows={2}
                        placeholder={t('register.message.placeholder')}
                        onChange={e => updateEp({ message: e.target.value })}
                        className={`${inputClass} resize-none`} />
                    </div>

                    {/* Group code — v1.0.0k #4: three-way radio.
                        Previously a two-way 'same' vs 'own' where
                        selecting 'own' revealed an empty text field;
                        leaving it blank meant "no code" but that was
                        not visually obvious. The new 'none' option
                        makes opting out an explicit, conscious
                        choice. 'own' now only fires when the user
                        actually intends to type a different code. */}
                    <div className="border border-steel-blue/20 rounded-xl p-3 bg-steel-blue/5 space-y-2">
                      <p className="text-xs font-semibold text-deep-navy">{t('register.group_code_for_person')}</p>
                      <label className="flex items-start gap-2 cursor-pointer">
                        <input type="radio" name={`gc_mode_${idx}`} value="same"
                          checked={ep.groupCodeMode === 'same'}
                          onChange={() => updateEp({ groupCodeMode: 'same', group_code: '' })}
                          className="mt-0.5 h-4 w-4 text-steel-blue" />
                        <span className="text-xs text-gray-700">
                          {t('register.group_code_same').replace('{name}', formData.first_name || t('register.primary_person'))}
                          <span className="block text-gray-400 mt-0.5">{t('register.group_code_same.hint')}</span>
                        </span>
                      </label>
                      <label className="flex items-start gap-2 cursor-pointer">
                        <input type="radio" name={`gc_mode_${idx}`} value="none"
                          checked={ep.groupCodeMode === 'none'}
                          onChange={() => updateEp({ groupCodeMode: 'none', group_code: '' })}
                          className="mt-0.5 h-4 w-4 text-steel-blue" />
                        <span className="text-xs text-gray-700">{t('register.group_code_none')}</span>
                      </label>
                      <label className="flex items-start gap-2 cursor-pointer">
                        <input type="radio" name={`gc_mode_${idx}`} value="own"
                          checked={ep.groupCodeMode === 'own'}
                          onChange={() => updateEp({ groupCodeMode: 'own' })}
                          className="mt-0.5 h-4 w-4 text-steel-blue" />
                        <span className="text-xs text-gray-700">{t('register.group_code_own')}</span>
                      </label>
                      {ep.groupCodeMode === 'own' && (
                        <input type="text" value={ep.group_code || ''}
                          placeholder={t('register.group_code.placeholder')}
                          onChange={e => updateEp({ group_code: e.target.value })}
                          className={inputClass} />
                      )}
                    </div>

                    {/* GDPR */}
                    <div className={extraPersonErrors[idx]?.gdpr_consent
                      ? "flex items-start gap-3 bg-burgundy/10 border border-burgundy rounded-lg p-3"
                      : "flex items-start gap-3 bg-gray-50 rounded-lg p-3"}>
                      <input type="checkbox" checked={ep.gdpr_consent} required
                        onChange={e => updateEp({ gdpr_consent: e.target.checked })}
                        className="mt-0.5 h-4 w-4 text-steel-blue border-gray-300 rounded" />
                      <label className="text-xs text-gray-600 leading-relaxed">
                        {t('register.gdpr')} <span style={{ color: 'var(--alert-burgundy)' }}>*</span>
                      </label>
                    </div>
                  </div>
                )}
              </div>
            );
          })}

          {/* Add another person — limit 10 total */}
          {extraPersons.length < 9 && (
            <button type="button"
              onClick={() => {
                // v0.58i-2: gender is per-person like name/surname/DOB.
                // Was previously pre-filled from primary which made the
                // dropdown look "carried over" — user may not change it.
                // Toggle copy logic at line ~549 already excludes gender;
                // this just brings the initial state into line.
                // Email + phone/address/country/church_organisation
                // pre-fill kept — handled by the existing toggle and
                // commonly shared across families.
                const newEp = {
                  first_name: '', last_name: '', email: formData.email || '',
                  gender: '', date_of_birth: '',
                  phone: formData.phone || '', address: formData.address || '',
                  country: formData.country || '', church_organisation: formData.church_organisation || '',
                  message: '', gdpr_consent: false, copyFromPrimary: true,
                  // v1.0.0k #4: group-code mode now has three options.
                  // 'same' (default): inherit primary's code (or no code
                  // if primary has none). 'none': explicitly opt out for
                  // this person. 'own': enter a different code in the
                  // text field. The 'none' option makes "no code" a
                  // conscious choice rather than implicit-when-blank,
                  // which was the previous behaviour.
                  groupCodeMode: 'same', // 'same' | 'none' | 'own'
                  group_code: '',
                  // v1.0.0k #5: per-extra-person custom field values.
                  // Mirrors the primary's customValues shape — keyed by
                  // custom_field.id. Previously the extra-person card
                  // never rendered custom fields, so any per-person
                  // event-specific question (allergies, room
                  // preference, role) was lost for participants 2–10.
                  customValues: {},
                };
                const next = [...extraPersons, newEp];
                setExtraPersons(next);
                setExtraPersonErrors([...extraPersonErrors, {}]);
                saveDraft({ extraPersons: next });
              }}
              className="mt-3 w-full border border-dashed border-gray-300 text-gray-500 hover:border-steel-blue hover:text-steel-blue text-xs font-medium py-2.5 rounded-xl transition-colors">
              + {t('register.add_person')}
              {extraPersons.length > 0 && <span className="text-gray-300 ml-1">({extraPersons.length + 1}/10)</span>}
            </button>
          )}

          {/* Second register button — visible when extra persons added */}
          {extraPersons.length > 0 && (
            <button type="submit" form="register-form" disabled={submitting}
              className={`mt-4 w-full text-white font-semibold py-3 rounded-lg transition-colors disabled:opacity-50 text-sm ${hasCustomStyle ? '' : 'bg-steel-blue hover:bg-mid-navy'}`}
              style={hasCustomStyle ? { backgroundColor: cs.primaryColor, borderRadius: radius } : {}}>
              {submitting ? t('register.submitting') : t('register.submit_group').replace('{n}', extraPersons.length + 1)}
            </button>
          )}
        </div>

        <div className="flex justify-center mt-5 mb-2">
            <div className="relative inline-flex items-center bg-gold border-2 border-gold rounded-lg overflow-hidden">
              <span className="pl-3 text-deep-navy text-sm pointer-events-none">🌐</span>
              <select value={lang} onChange={e => setLangOverride(e.target.value)}
                style={{ background: 'transparent' }}
                className="appearance-none text-[13px] font-semibold text-deep-navy pl-1.5 pr-7 py-1.5 cursor-pointer focus:outline-none">
                {SUPPORTED_LANGS.map(l => (
                  <option key={l.code} value={l.code} style={{ background: '#1e3a5f', color: 'white' }}>{l.label}</option>
                ))}
              </select>
              <span className="absolute right-2 text-deep-navy text-[10px] pointer-events-none">▼</span>
            </div>
          </div>
          <p className="text-center text-xs text-gray-300 mt-2">
            {/* v1.0-pre #19: link "Powered by Moimio" footer to moimio.app
                so anyone who's curious about the platform behind the form
                lands on the product page in a new tab. opener-isolated
                for safety since this page is unauthenticated. */}
            <a
              href="https://moimio.app"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline hover:text-white transition-colors"
            >
              {t('app.powered_by')}
            </a>
          </p>
      </div>
    </div>
  );
}

// Outer wrapper — provides I18nProvider so RegisterPage works without AuthProvider
export default function RegisterPage() {
  // v0.53.1: The public registration form is for participants, not the
  // organiser — it must NEVER inherit the admin's dark-mode preference.
  // Dark mode is applied via `document.documentElement.classList.add('dark')`
  // by ThemeProvider at the app root. Since the HTML class is global, any
  // route — including this public form — would otherwise render with dark
  // CSS variables on its light-themed card, producing unreadable text in
  // inputs and dropdowns. So while this page is mounted we temporarily
  // remove the class, and on unmount we restore it (the user's admin tab,
  // if any, will go back to dark when they navigate away).
  useEffect(() => {
    if (typeof document === 'undefined') return;
    const root = document.documentElement;
    const wasDark = root.classList.contains('dark');
    if (wasDark) root.classList.remove('dark');
    return () => {
      if (wasDark) root.classList.add('dark');
    };
  }, []);

  return (
    <I18nProvider forRegistration={true}>
      {/* colorScheme: light tells the browser to render native widgets
          (date pickers, dropdown options, scrollbars) in their light
          variants, even if the OS is in dark mode. */}
      <div style={{ colorScheme: 'light' }}>
        <RegisterForm />
      </div>
    </I18nProvider>
  );
}
