import { useState } from 'react';
import { useI18n } from '../hooks/useI18n';

const DEFAULT_STYLES = {
  primaryColor: '#4682B4',
  accentColor: '#FFD700',
  bgColor: '#F7F5F2',
  textColor: '#0F1E2E',
  borderRadius: '12',
  fontFamily: 'Nunito Sans',
};

const GOOGLE_FONTS = [
  'Nunito Sans', 'Inter', 'Lato', 'Open Sans', 'Roboto', 'Poppins',
  'Montserrat', 'Source Sans 3', 'Merriweather', 'Playfair Display',
  'Lora', 'Raleway', 'PT Sans', 'Work Sans', 'Noto Sans',
  'DM Sans', 'IBM Plex Sans', 'Outfit', 'Cabin', 'Barlow',
];

const COLOR_PRESETS = [
  { name: 'Moimio', primary: '#4682B4', accent: '#FFD700', bg: '#F7F5F2', text: '#0F1E2E' },
  { name: 'Living Water', primary: '#1B6B93', accent: '#7EC8E3', bg: '#F0F8FC', text: '#0A3D5C', verse: 'John 4:14' },
  { name: 'Mustard Seed', primary: '#9E6B1E', accent: '#D4A847', bg: '#FFFBF0', text: '#4A3012', verse: 'Matthew 17:20' },
  { name: 'Cedar of Lebanon', primary: '#2D6A4F', accent: '#8AB17D', bg: '#F2F8F5', text: '#1B4332', verse: 'Psalm 92:12' },
  { name: 'Lily of the Valley', primary: '#7B5EA7', accent: '#C9A7D8', bg: '#FBF5FF', text: '#3B0764', verse: 'Song of Solomon 2:1' },
  { name: 'Olive Branch', primary: '#5C6B3C', accent: '#A8B968', bg: '#F9FAF3', text: '#2D3520', verse: 'Genesis 8:11' },
  { name: 'Morning Star', primary: '#2E3A7A', accent: '#C9A33C', bg: '#F5F5FA', text: '#1A1F4B', verse: 'Revelation 22:16' },
];

export default function StyleCustomiser({ event, onSave, onClose }) {
  const { t } = useI18n();
  const saved = event?.settings?.style || {};
  const [styles, setStyles] = useState({
    primaryColor: saved.primaryColor || DEFAULT_STYLES.primaryColor,
    accentColor: saved.accentColor || DEFAULT_STYLES.accentColor,
    bgColor: saved.bgColor || DEFAULT_STYLES.bgColor,
    textColor: saved.textColor || DEFAULT_STYLES.textColor,
    borderRadius: saved.borderRadius || DEFAULT_STYLES.borderRadius,
    fontFamily: saved.fontFamily || DEFAULT_STYLES.fontFamily,
  });
  const [copied, setCopied] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savedMsg, setSavedMsg] = useState(false);

  const applyPreset = (preset) => {
    setStyles(prev => ({ ...prev, primaryColor: preset.primary, accentColor: preset.accent, bgColor: preset.bg, textColor: preset.text }));
  };

  const resetDefaults = () => setStyles({ ...DEFAULT_STYLES });

  const fontImportUrl = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(styles.fontFamily)}:wght@400;600;700&display=swap`;

  const generateCSS = () => `/* Moimio Registration Form — Custom Styles */
@import url('${fontImportUrl}');

:root {
  --moimio-primary: ${styles.primaryColor};
  --moimio-accent: ${styles.accentColor};
  --moimio-bg: ${styles.bgColor};
  --moimio-text: ${styles.textColor};
  --moimio-radius: ${styles.borderRadius}px;
  --moimio-font: '${styles.fontFamily}', sans-serif;
}

iframe[title*="Registration"] {
  border-radius: ${styles.borderRadius}px;
  max-width: 600px;
  width: 100%;
}`;

  const handleCopyCSS = async () => {
    try { await navigator.clipboard.writeText(generateCSS()); }
    catch { const t = document.createElement('textarea'); t.value = generateCSS(); t.style.position = 'fixed'; t.style.opacity = '0'; document.body.appendChild(t); t.select(); document.execCommand('copy'); document.body.removeChild(t); }
    setCopied(true); setTimeout(() => setCopied(false), 2000);
  };

  const inputClass = "w-full border border-card rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-steel-blue";

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-card-solid rounded-xl shadow-lg w-full max-w-3xl max-h-[85vh] flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="px-5 py-3 border-b border-card flex items-center justify-between shrink-0">
          <h3 className="font-heading font-bold text-body">{t('style.title')}</h3>
          <button onClick={onClose} className="text-subtle hover:text-muted text-lg">✕</button>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              {/* Presets */}
              <div>
                <label className="block text-xs font-semibold text-muted mb-2">{t('style.presets')}</label>
                <div className="grid grid-cols-2 gap-2">
                  {COLOR_PRESETS.map(preset => (
                    <button key={preset.name} onClick={() => applyPreset(preset)}
                      className="text-left p-2 rounded-lg border border-card hover:border-card transition-colors">
                      <div className="flex gap-1 mb-1">
                        <div className="w-4 h-4 rounded-full" style={{ background: preset.primary }} />
                        <div className="w-4 h-4 rounded-full" style={{ background: preset.accent }} />
                        <div className="w-4 h-4 rounded-full border" style={{ background: preset.bg }} />
                      </div>
                      <span className="text-[10px] text-muted font-medium">{preset.name}</span>
                      {preset.verse && <span className="text-[8px] text-subtle block">{preset.verse}</span>}
                    </button>
                  ))}
                </div>
              </div>

              {/* Colour pickers */}
              <div className="grid grid-cols-2 gap-3">
                {[
                  [t('style.primary'), 'primaryColor'], [t('style.accent'), 'accentColor'],
                  [t('style.background'), 'bgColor'], [t('style.text'), 'textColor'],
                ].map(([label, key]) => (
                  <div key={key}>
                    <label className="block text-[10px] text-muted mb-1">{label}</label>
                    <div className="flex gap-2 items-center">
                      <input type="color" value={styles[key]}
                        onChange={e => setStyles(p => ({ ...p, [key]: e.target.value }))}
                        className="w-8 h-8 rounded cursor-pointer border-0" />
                      <input type="text" value={styles[key]}
                        onChange={e => setStyles(p => ({ ...p, [key]: e.target.value }))}
                        className={inputClass} />
                    </div>
                  </div>
                ))}
              </div>

              {/* Border radius */}
              <div>
                <label className="block text-[10px] text-muted mb-1">{t('style.radius')}: {styles.borderRadius}px</label>
                <input type="range" min="0" max="24" value={styles.borderRadius}
                  onChange={e => setStyles(p => ({ ...p, borderRadius: e.target.value }))}
                  className="w-full" />
              </div>

              {/* Google Font */}
              <div>
                <label className="block text-[10px] text-muted mb-1">{t('style.font')}</label>
                <select value={styles.fontFamily}
                  onChange={e => setStyles(p => ({ ...p, fontFamily: e.target.value }))}
                  className={inputClass}>
                  {GOOGLE_FONTS.map(f => <option key={f} value={f}>{f}</option>)}
                </select>
                <p className="text-[8px] text-subtle mt-0.5">{t('style.font_hint')}</p>
              </div>
            </div>

            {/* Preview */}
            <div>
              <label className="block text-xs font-semibold text-muted mb-2">{t('style.preview')}</label>
              <div className="rounded-xl overflow-hidden border border-card" style={{
                background: styles.bgColor, fontFamily: `'${styles.fontFamily}', sans-serif`, borderRadius: `${styles.borderRadius}px`,
              }}>
                <div className="p-4">
                  <h3 style={{ color: styles.textColor, fontWeight: 'bold', fontSize: '16px', marginBottom: '12px' }}>{t('event.registration_form')}</h3>
                  {['First Name *', 'Email *'].map(label => (
                    <div key={label} style={{ marginBottom: '8px' }}>
                      <label style={{ color: styles.textColor, fontSize: '12px', fontWeight: '600' }}>{label}</label>
                      <div style={{
                        border: '1px solid #ddd', borderRadius: `${Math.min(styles.borderRadius, 8)}px`,
                        padding: '6px 10px', fontSize: '12px', marginTop: '2px', background: 'white',
                      }}>{label === 'First Name *' ? 'Johannes' : 'email@example.com'}</div>
                    </div>
                  ))}
                  <div style={{
                    background: styles.primaryColor, color: 'white', textAlign: 'center',
                    padding: '8px', borderRadius: `${Math.min(styles.borderRadius, 8)}px`,
                    fontSize: '12px', fontWeight: 'bold', marginTop: '12px',
                  }}>{t('register.submit')}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Generated CSS */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-muted">{t('style.css')}</label>
              <button onClick={handleCopyCSS}
                className={`text-xs font-semibold px-3 py-1 rounded-lg transition-colors ${
                  copied ? 'bg-accent-tint text-accent' : 'bg-steel-blue text-white hover:bg-mid-navy'
                }`}>{copied ? t('style.copied') : t('style.copy_css')}</button>
            </div>
            <pre className="bg-neutral-tint rounded-lg px-4 py-3 text-[10px] font-mono text-muted overflow-x-auto border border-card whitespace-pre-wrap">
              {generateCSS()}
            </pre>
          </div>
        </div>

        <div className="px-5 py-3 border-t border-card flex items-center justify-between shrink-0">
          <button onClick={resetDefaults} className="text-xs text-subtle hover:text-muted">{t('style.reset')}</button>
          <div className="flex gap-2">
            <button onClick={onClose} className="text-xs text-subtle hover:text-muted px-3 py-2">{t('common.cancel')}</button>
            <button onClick={async () => {
              setSaving(true);
              try {
                if (onSave) await onSave(styles);
                setSavedMsg(true);
                setTimeout(() => { setSavedMsg(false); onClose(); }, 800);
              } catch {} finally { setSaving(false); }
            }} disabled={saving}
              className={`text-xs font-semibold px-4 py-2 rounded-lg transition-colors bg-steel-blue text-white hover:bg-mid-navy disabled:opacity-50`}>
              {savedMsg ? t('style.saved') : saving ? t('style.saving') : t('style.save')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
