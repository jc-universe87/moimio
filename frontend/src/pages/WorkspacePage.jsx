import { useEffect, useState } from 'react';
import { dangerZone as dangerZoneApi, workspaceSettings as workspaceSettingsApi } from '../services/api';
import { useI18n } from '../hooks/useI18n';
import { useAuth } from '../hooks/useAuth';
import { useCapabilities } from '../hooks/useCapabilities';
import DangerZoneDeletionModal from '../components/DangerZoneDeletionModal';
import TranslatedError from '../components/TranslatedError';

/**
 * WorkspacePage — `/admin/workspace`.
 *
 * Super-admin-only workspace-level settings page. Two sections:
 *
 *   1. Privacy notice (LEGAL-1, both editions). The web address of the
 *      ORGANISATION's own privacy notice. When set, the public registration
 *      form shows a link to it after the consent sentence. Stored in the
 *      one-row `workspace_settings` table; validated on the server as an
 *      absolute http(s) URL and refused with a visible message otherwise,
 *      because a form that saves nothing and says nothing is worse than
 *      no form (FORM-2).
 *
 *   2. Danger Zone (hosted only). Customer-triggered workspace deletion.
 *      Gated on `capabilities.account_portal`, the managed-instance signal,
 *      the same gate the sidebar used to put on this whole page. A
 *      self-hoster has no SaaS endpoint, so the request would be a no-op
 *      for them; it is hidden rather than offered.
 *
 * The deletion flow:
 *   1. Super admin clicks "Delete workspace" → modal opens.
 *   2. Modal: user reads the timeline, types DELETE, clicks Confirm.
 *   3. Frontend calls `dangerZone.requestDeletion("DELETE")` →
 *      backend queues a `workspace.delete_requested` event for the SaaS.
 *   4. SaaS receives the event, generates the export, stamps clocks,
 *      stops the tenant container (customer is logged out shortly after).
 *   5. Customer receives email with download link.
 *
 * Once the SaaS pauses the tenant, the container goes down — so the
 * "success" view in the modal is the last thing the customer sees in
 * CE. The actual deletion is asynchronous; we don't poll for it.
 *
 * Hidden in the sidebar for staff and event-admins.
 */
export default function WorkspacePage() {
  const { t } = useI18n();
  const { user } = useAuth();
  const { capabilities } = useCapabilities();
  const [modalOpen, setModalOpen] = useState(false);

  const isSuperAdmin = user?.role === 'super_admin';
  // Standing in for an explicit hosted flag; see LegalNotice / AdminLayout.
  const isHostedEdition = capabilities.account_portal === true;

  // LEGAL-1 — the privacy notice URL field.
  const [privacyUrl, setPrivacyUrl] = useState('');
  const [privacyLoaded, setPrivacyLoaded] = useState(false);
  const [privacySaving, setPrivacySaving] = useState(false);
  const [privacySaved, setPrivacySaved] = useState(false);
  const [privacyError, setPrivacyError] = useState(null);

  useEffect(() => {
    if (!isSuperAdmin) return;
    let cancelled = false;
    (async () => {
      try {
        const data = await workspaceSettingsApi.get();
        if (!cancelled) setPrivacyUrl(data?.privacy_notice_url || '');
      } catch (err) {
        if (!cancelled) setPrivacyError(err);
      } finally {
        if (!cancelled) setPrivacyLoaded(true);
      }
    })();
    return () => { cancelled = true; };
  }, [isSuperAdmin]);

  const handlePrivacySubmit = async (e) => {
    e.preventDefault();
    if (privacySaving) return;
    setPrivacySaving(true);
    setPrivacySaved(false);
    setPrivacyError(null);
    try {
      const data = await workspaceSettingsApi.update({ privacy_notice_url: privacyUrl });
      setPrivacyUrl(data?.privacy_notice_url || '');
      setPrivacySaved(true);
    } catch (err) {
      // The server answers a bad address with a translatable key; the
      // banner below says so. Nothing is stored in that case.
      setPrivacyError(err);
    } finally {
      setPrivacySaving(false);
    }
  };

  if (!isSuperAdmin) {
    // Sidebar nav hides this entry for non-super-admins, but a direct
    // URL hit lands here. Show a non-alarming "not for you" message
    // rather than a 403-feeling error banner.
    return (
      <div className="max-w-3xl mx-auto p-6">
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          {t('errors.workspace.super_admin_only')}
        </p>
      </div>
    );
  }

  const handleSubmit = async (confirmation) => {
    // The API expects the canonical English token "DELETE" — the modal
    // normalises whatever the user typed before invoking us, so this is
    // a straight pass-through. Errors propagate to the modal's banner.
    return dangerZoneApi.requestDeletion(confirmation);
  };

  const inputClass = "rounded-card border bg-[var(--app-bg)] border-[var(--card-border)] text-[var(--text-primary)] px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--io-accent)]";

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <header>
        <h1 className="font-heading font-bold text-2xl" style={{ color: 'var(--text-primary)' }}>
          {t('workspace.page.title')}
        </h1>
      </header>

      {/* Privacy notice section (LEGAL-1) */}
      <section
        className="card-surface-solid rounded-2xl overflow-hidden"
        style={{ border: '1px solid var(--card-border)' }}
      >
        <div
          className="px-5 py-3"
          style={{ borderBottom: '1px solid var(--card-border)' }}
        >
          <h2 className="font-heading font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
            {t('workspace.privacy.title')}
          </h2>
        </div>

        <form className="p-5 space-y-3" onSubmit={handlePrivacySubmit} noValidate>
          <label className="block text-sm font-semibold" htmlFor="privacy-notice-url"
            style={{ color: 'var(--text-primary)' }}>
            {t('workspace.privacy.label')}
          </label>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            {t('workspace.privacy.help')}
          </p>
          <input
            id="privacy-notice-url"
            name="privacy_notice_url"
            type="url"
            inputMode="url"
            autoComplete="off"
            placeholder="https://example.org/privacy"
            value={privacyUrl}
            disabled={!privacyLoaded || privacySaving}
            aria-invalid={!!privacyError}
            onChange={(e) => { setPrivacyUrl(e.target.value); setPrivacySaved(false); setPrivacyError(null); }}
            className={`w-full ${inputClass}`}
          />
          <TranslatedError err={privacyError} variant="compact" />
          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={!privacyLoaded || privacySaving}
              className="text-sm font-semibold px-4 py-2 rounded-card bg-steel-blue text-white hover:bg-steel-blue-700 transition-colors disabled:opacity-60 disabled:cursor-wait"
            >
              {privacySaving ? t('common.saving') : t('common.save')}
            </button>
            {privacySaved && (
              <span className="text-sm" role="status" style={{ color: 'var(--text-muted)' }}>
                {t('common.saved')}
              </span>
            )}
          </div>
        </form>
      </section>

      {/* Danger Zone section — hosted only */}
      {isHostedEdition && (
        <section
          className="card-surface-solid rounded-2xl overflow-hidden"
          style={{ border: '1px solid var(--alert-burgundy)' }}
        >
          <div
            className="px-5 py-3"
            style={{ borderBottom: '1px solid var(--card-border)' }}
          >
            <h2 className="font-heading font-semibold text-sm" style={{ color: 'var(--alert-burgundy)' }}>
              {t('danger_zone.section.title')}
            </h2>
          </div>

          <div className="p-5">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
              <div className="min-w-0 flex-1">
                <h3 className="font-heading font-semibold text-base mb-1" style={{ color: 'var(--text-primary)' }}>
                  {t('danger_zone.delete.heading')}
                </h3>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  {t('danger_zone.delete.body')}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setModalOpen(true)}
                className="shrink-0 text-sm font-semibold px-4 py-2 rounded-card transition-colors"
                style={{ background: 'var(--alert-burgundy)', color: '#fff' }}
              >
                {t('danger_zone.delete.button')}
              </button>
            </div>
          </div>
        </section>
      )}

      {isHostedEdition && (
        <DangerZoneDeletionModal
          open={modalOpen}
          onSubmit={handleSubmit}
          onClose={() => setModalOpen(false)}
          userEmail={user?.email}
        />
      )}
    </div>
  );
}
