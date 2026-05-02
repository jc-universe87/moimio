import { useState } from 'react';
import { useI18n } from '../hooks/useI18n';

export default function SharePanel({ eventId, event }) {
  const [copied, setCopied] = useState(null);
  const { t } = useI18n();

  const regUrl = `${window.location.origin}/register/${eventId}`;
  const style = event?.settings?.style;

  const buildEmbedCode = () => {
    let styleBlock = '';
    if (style) {
      const fontUrl = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(style.fontFamily || 'Nunito Sans')}:wght@400;600;700&display=swap`;
      styleBlock = `\n<style>\n  @import url('${fontUrl}');\n  .moimio-embed {\n    --moimio-primary: ${style.primaryColor || '#4682B4'};\n    --moimio-bg: ${style.bgColor || '#F7F5F2'};\n  }\n</style>\n`;
    }
    return `${styleBlock}<iframe\n  src="${regUrl}"\n  width="100%"\n  height="800"\n  frameborder="0"\n  style="border: none; border-radius: ${style?.borderRadius || 12}px; max-width: 600px;"\n  title="Registration — ${event?.name || 'Event'}"\n></iframe>`;
  };

  const embedCode = buildEmbedCode();

  const handleCopy = async (text, type) => {
    try { await navigator.clipboard.writeText(text); }
    catch {
      const el = document.createElement('textarea');
      el.value = text; el.style.position = 'fixed'; el.style.opacity = '0';
      document.body.appendChild(el); el.select(); document.execCommand('copy');
      document.body.removeChild(el);
    }
    setCopied(type);
    setTimeout(() => setCopied(null), 2000);
  };

  // v0.70d-2d-2 (S10): when registration isn't open, render nothing.
  // The gate card at the bottom of SetupHub already explains the
  // state ("Open registration when ready" etc.) — having a second
  // hint above the Save button duplicated the signal.
  if (event?.status !== 'open') {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="bg-neutral-tint rounded-xl p-4">
        <div className="flex items-center justify-between mb-2 gap-2">
          <h4 className="text-sm font-semibold text-body">{t('event.share.link_title')}</h4>
          <div className="flex items-center gap-2 shrink-0">
            {/* v1.0-pre #18: direct "Open" link to the registration page,
                so admins can preview their public form in one click without
                having to copy-paste the URL into a new tab. Opens in a new
                tab so the admin's session isn't affected. */}
            <a
              href={regUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-semibold px-3 py-1 rounded-lg border border-card hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
              style={{ color: 'var(--text-muted)' }}
            >
              {t('event.share.open_link')} ↗
            </a>
            <button onClick={() => handleCopy(regUrl, 'link')}
              className={`text-xs font-semibold px-3 py-1 rounded-lg transition-colors ${copied === 'link' ? 'bg-accent-tint text-accent' : 'bg-steel-blue text-white hover:bg-mid-navy'}`}>
              {copied === 'link' ? t('event.share.copied_link') : t('event.share.copy_link')}
            </button>
          </div>
        </div>
        <div className="bg-card-solid rounded-lg px-3 py-2 text-xs font-mono text-muted break-all border border-card">{regUrl}</div>
        <p className="text-[10px] text-subtle mt-1">{t('event.share.link_hint')}</p>
      </div>

      <div className="bg-neutral-tint rounded-xl p-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-semibold text-body">{t('event.share.embed_title')}</h4>
          <button onClick={() => handleCopy(embedCode, 'embed')}
            className={`text-xs font-semibold px-3 py-1 rounded-lg transition-colors ${copied === 'embed' ? 'bg-accent-tint text-accent' : 'bg-steel-blue text-white hover:bg-mid-navy'}`}>
            {copied === 'embed' ? t('event.share.copied_link') : t('event.share.copy_embed')}
          </button>
        </div>
        <pre className="bg-card-solid rounded-lg px-3 py-2 text-[10px] font-mono text-muted overflow-x-auto border border-card whitespace-pre-wrap">{embedCode}</pre>
        <p className="text-[10px] text-subtle mt-1">
          {t('event.share.embed_hint')}
          {style && <span className="text-accent"> {t('style.custom_included')}</span>}
        </p>
      </div>
    </div>
  );
}
