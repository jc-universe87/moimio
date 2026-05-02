import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useDateFormat } from '../hooks/useDateFormat';
import { useI18n, SUPPORTED_LANGS } from '../hooks/useI18n';
import Wordmark from '../components/Wordmark';
import ThemeToggle from '../components/ThemeToggle';

// v0.59a-1: same auto-derivation pattern as AdminLayout sidebar.
// See vite.config.js `define` for the build-time source of truth
// (frontend/package.json::moimioVersion). Fallback 'dev' for tests.
const MOIMIO_VERSION = typeof __MOIMIO_VERSION__ !== 'undefined' ? __MOIMIO_VERSION__ : 'dev';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);
  const { login } = useAuth();
  const { reloadPrefs } = useDateFormat();
  const { t, lang, setLang } = useI18n();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null); setLoading(true);
    try {
      await login(email, password);
      reloadPrefs();
      navigate('/admin');
    } catch (err) {
      // v0.70d-2b (R6): split the error surface by category.
      // - Network failure → "Could not reach the server" (actionable:
      //   check connection / retry).
      // - HTTP error (any status) → the deliberately ambiguous
      //   "Email or password is incorrect" from v0.57's anti-
      //   enumeration hardening. Even a 500 falls through to this
      //   bucket: we don't want to leak server state to unauthenticated
      //   clients, and "try again" without more info is a reasonable
      //   thing to ask the user to do.
      setError(err?.isNetwork ? 'network' : 'credentials');
    }
    finally { setLoading(false); }
  };

  const inputClass = "w-full rounded-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-steel-blue " +
                     "bg-white dark:bg-white/5 border border-card " +
                     "text-body";

  return (
    <div className="min-h-screen flex items-center justify-center p-4"
         style={{ backgroundColor: 'var(--app-bg)' }}>
      {/* Theme toggle in top-right corner — per §9.8 public pages get toggle too */}
      <div className="fixed top-[calc(0.75rem+env(safe-area-inset-top))] right-[calc(0.75rem+env(safe-area-inset-right))]">
        <ThemeToggle tone="inline" />
      </div>

      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <img src="/logogram.svg" alt="Moimio" className="w-16 h-16 mx-auto mb-4" />
          <Wordmark size="lg" withTagline className="text-center" />
        </div>

        <div className="card-surface-solid p-6">
          <h2 className="font-heading font-bold text-lg mb-4"
              style={{ color: 'var(--text-primary)' }}>
            {t('login.title')}
          </h2>

          {error && (
            <div className="bg-alert-tint text-alert border border-alert text-xs rounded-card p-2 mb-4">
              {error === 'network' ? t('login.error.network') : t('login.error')}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold mb-1"
                     style={{ color: 'var(--text-muted)' }}>{t('login.email')}</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} required autoFocus
                     className={inputClass} />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1"
                     style={{ color: 'var(--text-muted)' }}>{t('login.password')}</label>
              <div className="relative">
                <input type={showPw ? 'text' : 'password'} value={password}
                       onChange={e => setPassword(e.target.value)} required
                       className={`${inputClass} pr-16`} />
                <button type="button" onClick={() => setShowPw(v => !v)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] hover:text-deep-navy dark:hover:text-off-white"
                        style={{ color: 'var(--text-subtle)' }}>
                  {showPw ? t('common.hide') : t('common.show')}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading}
                    className="w-full bg-steel-blue text-white font-semibold py-2.5 rounded-card hover:bg-steel-blue-700 transition-colors disabled:opacity-50">
              {loading ? t('login.submitting') : t('login.submit')}
            </button>
          </form>

          <div className="mt-4 text-center">
            <button type="button" onClick={() => window.location.href = '/forgot-password'}
                    className="text-xs hover:text-steel-blue transition-colors bg-transparent border-none cursor-pointer"
                    style={{ color: 'var(--text-subtle)' }}>
              {t('login.forgot')}
            </button>
          </div>
        </div>

        <div className="flex justify-center mt-5">
          <div className="relative inline-flex items-center bg-gold border-2 border-gold rounded-card overflow-hidden">
            <span className="pl-3 text-deep-navy text-sm pointer-events-none">🌐</span>
            <select value={lang} onChange={e => setLang(e.target.value)}
                    style={{ background: 'transparent' }}
                    className="appearance-none text-[13px] font-semibold text-deep-navy pl-1.5 pr-7 py-1.5 cursor-pointer focus:outline-none">
              {SUPPORTED_LANGS.map(l => (
                <option key={l.code} value={l.code} style={{ background: '#1e3a5f', color: 'white' }}>{l.label}</option>
              ))}
            </select>
            <span className="absolute right-2 text-deep-navy text-[10px] pointer-events-none">▼</span>
          </div>
        </div>
        <p className="text-center text-[10px] mt-2" style={{ color: 'var(--text-subtle)' }}>
          {t('app.verse')}
        </p>
        <p className="text-center text-[10px] mt-1" style={{ color: 'var(--text-subtle)' }}>
          {MOIMIO_VERSION} · © Pistio
        </p>
      </div>
    </div>
  );
}
