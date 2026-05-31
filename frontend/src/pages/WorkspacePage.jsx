import { useState } from 'react';
import { dangerZone as dangerZoneApi } from '../services/api';
import { useI18n } from '../hooks/useI18n';
import { useAuth } from '../hooks/useAuth';
import DangerZoneDeletionModal from '../components/DangerZoneDeletionModal';

/**
 * WorkspacePage — `/admin/workspace`.
 *
 * Super-admin-only workspace-level settings page. Today it houses one
 * section: the Danger Zone for customer-triggered workspace deletion.
 * Future workspace-level settings (rename, branding, billing contact)
 * can land here as additional sections.
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
 * Self-hosters (no SaaS endpoint configured): the request returns 202
 * but `queue_event` is a no-op (zero subscribed endpoints). The success
 * state still renders — for a self-hoster, deletion is whatever they
 * choose to do with their own database afterwards. We acknowledge the
 * customer's intent, no more.
 *
 * Hidden in the sidebar for staff and event-admins.
 */
export default function WorkspacePage() {
  const { t } = useI18n();
  const { user } = useAuth();
  const [modalOpen, setModalOpen] = useState(false);

  const isSuperAdmin = user?.role === 'super_admin';

  if (!isSuperAdmin) {
    // Sidebar nav hides this entry for non-super-admins, but a direct
    // URL hit lands here. Show a non-alarming "not for you" message
    // rather than a 403-feeling error banner.
    return (
      <div className="max-w-3xl mx-auto p-6">
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          {t('errors.danger_zone.super_admin_only')}
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

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <header>
        <h1 className="font-heading font-bold text-2xl" style={{ color: 'var(--text-primary)' }}>
          {t('workspace.page.title')}
        </h1>
      </header>

      {/* Danger Zone section */}
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

      <DangerZoneDeletionModal
        open={modalOpen}
        onSubmit={handleSubmit}
        onClose={() => setModalOpen(false)}
        userEmail={user?.email}
      />
    </div>
  );
}
