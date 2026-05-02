import { useState } from 'react';
import { useI18n } from '../hooks/useI18n';
import { passwordReset } from '../services/api';
import Wordmark from '../components/Wordmark';
import ThemeToggle from '../components/ThemeToggle';
import TranslatedError from '../components/TranslatedError';

// v0.59a-1: see LoginPage for rationale and pattern source.
const MOIMIO_VERSION = typeof __MOIMIO_VERSION__ !== 'undefined' ? __MOIMIO_VERSION__ : 'dev';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState(null);
  const { t } = useI18n();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null); setLoading(true);
    try {
      await passwordReset.request(email);
      setSent(true);
    } catch (err) { setError(err); }
    finally { setLoading(false); }
  };

  const inputClass = "w-full rounded-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-steel-blue " +
                     "bg-white dark:bg-white/5 border border-card " +
                     "text-body";

  return (
    <div className="min-h-screen flex items-center justify-center p-4"
         style={{ backgroundColor: 'var(--app-bg)' }}>
      <div className="fixed top-[calc(0.75rem+env(safe-area-inset-top))] right-[calc(0.75rem+env(safe-area-inset-right))]">
        <ThemeToggle tone="inline" />
      </div>

      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <img src="/logogram.svg" alt="Moimio" className="w-16 h-16 mx-auto mb-4" />
          <Wordmark size="lg" />
        </div>
        <div className="card-surface-solid p-6">
          {sent ? (
            <div className="text-center">
              <div className="text-steel-blue text-4xl mb-3">✉</div>
              <h2 className="font-heading font-bold text-lg mb-2"
                  style={{ color: 'var(--text-primary)' }}>
                {t('forgot.success.title')}
              </h2>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                {t('forgot.success.message', { email })}
              </p>
              <p className="text-xs mt-4" style={{ color: 'var(--text-subtle)' }}>
                {t('forgot.success.spam')}
              </p>
              <button type="button" onClick={() => window.location.href = '/login'}
                      className="mt-5 inline-block text-xs text-steel-blue hover:text-steel-blue-700 font-semibold bg-transparent border-none cursor-pointer">
                {t('forgot.back')}
              </button>
            </div>
          ) : (
            <>
              <h2 className="font-heading font-bold text-lg mb-1"
                  style={{ color: 'var(--text-primary)' }}>
                {t('forgot.title')}
              </h2>
              <p className="text-xs mb-4" style={{ color: 'var(--text-subtle)' }}>
                {t('forgot.subtitle')}
              </p>
              <TranslatedError err={error} className="text-xs rounded-card p-2 mb-4" />
              <form onSubmit={handleSubmit} className="space-y-3">
                <div>
                  <label className="block text-xs font-semibold mb-1"
                         style={{ color: 'var(--text-muted)' }}>{t('login.email')}</label>
                  <input type="email" value={email} onChange={e => setEmail(e.target.value)} required autoFocus
                         className={inputClass} />
                </div>
                <button type="submit" disabled={loading}
                        className="w-full bg-steel-blue text-white font-semibold py-2.5 rounded-card hover:bg-steel-blue-700 transition-colors disabled:opacity-50">
                  {loading ? t('forgot.submitting') : t('forgot.submit')}
                </button>
              </form>
              <div className="mt-4 text-center">
                <button type="button" onClick={() => window.location.href = '/login'}
                        className="text-xs bg-transparent border-none cursor-pointer hover:text-deep-navy dark:hover:text-off-white"
                        style={{ color: 'var(--text-subtle)' }}>
                  {t('forgot.back')}
                </button>
              </div>
            </>
          )}
        </div>
        <p className="text-center text-[10px] mt-6" style={{ color: 'var(--text-subtle)' }}>
          {t('app.verse')}
        </p>
        <p className="text-center text-[10px] mt-1" style={{ color: 'var(--text-subtle)' }}>
          {MOIMIO_VERSION} · © Pistio
        </p>
      </div>
    </div>
  );
}
