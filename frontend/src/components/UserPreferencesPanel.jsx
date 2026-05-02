import { useState, useEffect } from 'react';
import { preferences as prefsApi } from '../services/api';
import { useDateFormat } from '../hooks/useDateFormat';
import { useI18n, SUPPORTED_LANGS } from '../hooks/useI18n';
import { useToast } from '../hooks/useToast';
import TimezonePicker from './TimezonePicker';

export default function UserPreferencesPanel({ onClose }) {
  const { t, lang, setLang } = useI18n();
  const { showToast, ToastHost } = useToast();
  // v0.50d-4: initialise language from the active UI language (set via
  // login page language picker or localStorage) rather than a hardcoded
  // 'en'. Otherwise the dropdown can disagree with the visibly-rendered
  // UI language, which looks like a bug even though nothing changed yet.
  const [prefs, setPrefs] = useState({ language: lang || 'en', date_format: 'DD/MM/YYYY', timezone: 'Europe/London' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const { updateFormat } = useDateFormat();

  useEffect(() => { loadPrefs(); }, []);

  const loadPrefs = async () => {
    try {
      const data = await prefsApi.get();
      // Merge backend prefs, but let the active i18n lang win if it
      // differs — the user's runtime choice (via login picker) is more
      // current than whatever is stored on the server.
      setPrefs({ ...data, language: lang || data.language || 'en' });
      // Keep the app's i18n only if localStorage has no explicit override
      // (preserves the existing behaviour for legacy users).
      if (data.language && !localStorage.getItem('moimio_lang')) setLang(data.language);
    } catch {} finally { setLoading(false); }
  };

  const handleSave = async () => {
    setSaving(true); setSaved(false);
    try {
      await prefsApi.update(prefs);
      updateFormat(prefs.date_format);
      setLang(prefs.language); // Switch app language immediately
      setSaved(true);
      // v0.70d-3a-4 (M1): success toast on save. Belt-and-braces
      // with the existing 2-second "Saved!" button-label flip — the
      // toast catches users who don't look at the button after
      // clicking it (the existing flip is subtle).
      showToast(t('prefs.saved'), 'success');
      setTimeout(() => setSaved(false), 2000);
    } catch {} finally { setSaving(false); }
  };

  if (loading) return <div className="p-3 text-xs text-white/40">{t("common.loading")}</div>;

  const selectClass = "w-full bg-white/5 text-white text-xs rounded px-2 py-1 border border-white/10 focus:outline-none focus:ring-1 focus:ring-steel-blue [color-scheme:dark]";

  return (
    <div className="p-3 border-t border-white/10 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-white/70">{t("prefs.title")}</span>
        <button onClick={onClose} className="text-[10px] text-white/40 hover:text-white">✕</button>
      </div>
      <div>
        <label className="block text-[10px] text-white/40 mb-0.5">{t("prefs.language")}</label>
        <select value={prefs.language} onChange={e => { setPrefs(p => ({ ...p, language: e.target.value })); setLang(e.target.value); }} className={selectClass}>
          {SUPPORTED_LANGS.map(l => <option key={l.code} value={l.code} className="text-body bg-card-solid">{l.label}</option>)}
        </select>
      </div>
      <div>
        <label className="block text-[10px] text-white/40 mb-0.5">{t("prefs.date_format")}</label>
        <select value={prefs.date_format} onChange={e => setPrefs(p => ({ ...p, date_format: e.target.value }))} className={selectClass}>
          <option value="DD/MM/YYYY" className="text-body bg-card-solid">DD/MM/YYYY</option>
          <option value="MM/DD/YYYY" className="text-body bg-card-solid">MM/DD/YYYY</option>
          <option value="YYYY-MM-DD" className="text-body bg-card-solid">YYYY-MM-DD</option>
        </select>
      </div>
      <div>
        <label className="block text-[10px] text-white/40 mb-0.5">{t("prefs.timezone")}</label>
        {/* v0.70d-2b (R13): parity with DetailsEditor — TimezonePicker
            accepts any IANA zone via datalist autocomplete, replacing
            the previous 8-option hard-coded <select>. Uses the same
            sidebar-dark class as the sibling selects. */}
        <TimezonePicker
          value={prefs.timezone}
          onChange={v => setPrefs(p => ({ ...p, timezone: v }))}
          className={selectClass}
          ariaLabel={t('prefs.timezone')}
        />
      </div>
      <button onClick={handleSave} disabled={saving}
        className={`w-full text-xs font-semibold py-1.5 rounded transition-colors bg-steel-blue text-white hover:bg-mid-navy disabled:opacity-50`}>
        {saved ? t('prefs.saved') : saving ? t('prefs.saving') : t('prefs.save')}
      </button>
      <ToastHost />
    </div>
  );
}
