import { useState, useEffect, useCallback } from 'react';
import { outboundWebhooks as webhooksApi } from '../services/api';
import { useI18n } from '../hooks/useI18n';
import { useAuth } from '../hooks/useAuth';
import { useConfirmOverlay } from '../components/ConfirmOverlay';
import WebhookSecretModal from '../components/WebhookSecretModal';
import EmptyState from '../components/EmptyState';
import TranslatedError from '../components/TranslatedError';

/**
 * WebhooksPage — v1.0.0g.
 *
 * Admin section for managing outbound webhook endpoints. Hidden behind
 * `FEATURE_OUTBOUND_WEBHOOKS` at the backend, gated in the sidebar by
 * `useCapabilities().outbound_webhooks` on the frontend.
 *
 * SaaS-managed endpoints (`managed_by="saas"`) are filtered server-side
 * and never appear here — they are infrastructure, not user-managed.
 *
 * Styling: uses CE's CSS variable system (--app-bg, --card-bg-solid,
 * --text-primary, --io-accent, etc.), which flips automatically between
 * light and dark mode. No hardcoded colour values.
 */
export default function WebhooksPage() {
  const { t } = useI18n();
  const { user } = useAuth();
  const { confirm, ConfirmOverlay } = useConfirmOverlay();

  const [endpoints, setEndpoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [feedback, setFeedback] = useState(null);  // { kind: 'success'|'info', message: '...' }

  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: '', url: '', event_types: '*' });

  const [revealedSecret, setRevealedSecret] = useState(null);

  const [expandedId, setExpandedId] = useState(null);
  const [deliveries, setDeliveries] = useState({});
  const [loadingDeliveries, setLoadingDeliveries] = useState(false);

  const isSuperAdmin = user?.role === 'super_admin';

  const showFeedback = (message, kind = 'success') => {
    setFeedback({ kind, message });
    setTimeout(() => setFeedback(null), 4000);
  };

  const loadEndpoints = useCallback(async () => {
    setLoading(true);
    try {
      const data = await webhooksApi.list();
      setEndpoints(data);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isSuperAdmin) loadEndpoints();
  }, [isSuperAdmin, loadEndpoints]);

  const loadDeliveries = async (endpointId) => {
    setLoadingDeliveries(true);
    try {
      const data = await webhooksApi.listDeliveries(endpointId, 50);
      setDeliveries(prev => ({ ...prev, [endpointId]: data }));
    } catch (err) {
      setError(err);
    } finally {
      setLoadingDeliveries(false);
    }
  };

  const handleToggleExpand = async (endpointId) => {
    if (expandedId === endpointId) {
      setExpandedId(null);
      return;
    }
    setExpandedId(endpointId);
    if (!deliveries[endpointId]) {
      await loadDeliveries(endpointId);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setError(null);
    const event_types = form.event_types
      .split(',')
      .map(s => s.trim())
      .filter(Boolean);
    try {
      const created = await webhooksApi.create({
        name: form.name,
        url: form.url,
        event_types: event_types.length ? event_types : ['*'],
      });
      setRevealedSecret({
        name: created.name,
        url: created.url,
        secret: created.secret,
      });
      setForm({ name: '', url: '', event_types: '*' });
      setShowCreate(false);
      await loadEndpoints();
    } catch (err) {
      setError(err);
    }
  };

  // v1.0.0g UX: after firing a test, auto-open the deliveries panel and
  // poll for the result. The backend now triggers an immediate worker
  // tick synchronously, so the delivery is typically resolved by the
  // time the panel opens — but we poll twice with a small delay in case
  // the receiver is slow.
  const handleTest = async (endpoint) => {
    setError(null);
    try {
      await webhooksApi.sendTest(endpoint.id);
      showFeedback(t('webhooks.test_queued'), 'success');
      if (expandedId !== endpoint.id) {
        setExpandedId(endpoint.id);
      }
      // Backend ran a worker tick; refresh once now and once after 1s
      // to catch the result whether immediate or slightly delayed.
      await loadDeliveries(endpoint.id);
      setTimeout(() => loadDeliveries(endpoint.id), 1500);
      // Refresh the endpoint list too: state may have flipped to active
      // (if previously degraded) or last_success_at updated.
      await loadEndpoints();
    } catch (err) {
      setError(err);
    }
  };

  const handleTogglePause = async (endpoint) => {
    setError(null);
    try {
      await webhooksApi.update(endpoint.id, { is_active: !endpoint.is_active });
      await loadEndpoints();
    } catch (err) {
      setError(err);
    }
  };

  const handleReenable = async (endpoint) => {
    setError(null);
    try {
      await webhooksApi.reenable(endpoint.id);
      await loadEndpoints();
    } catch (err) {
      setError(err);
    }
  };

  const handleRotate = async (endpoint) => {
    const ok = await confirm({
      title: t('webhooks.rotate.confirm.title'),
      message: t('webhooks.rotate.confirm.message', { name: endpoint.name }),
      confirmLabel: t('webhooks.rotate.confirm.cta'),
      danger: true,
    });
    if (!ok) return;
    try {
      const rotated = await webhooksApi.rotateSecret(endpoint.id);
      setRevealedSecret({
        name: rotated.name,
        url: rotated.url,
        secret: rotated.secret,
      });
      await loadEndpoints();
    } catch (err) {
      setError(err);
    }
  };

  const handleDelete = async (endpoint) => {
    const ok = await confirm({
      title: t('webhooks.delete.confirm.title'),
      message: t('webhooks.delete.confirm.message', { name: endpoint.name }),
      confirmLabel: t('webhooks.delete.confirm.cta'),
      danger: true,
    });
    if (!ok) return;
    try {
      await webhooksApi.delete(endpoint.id);
      if (expandedId === endpoint.id) setExpandedId(null);
      await loadEndpoints();
    } catch (err) {
      setError(err);
    }
  };

  if (!isSuperAdmin) {
    return (
      <div className="p-6">
        <h1
          className="text-xl font-semibold mb-4"
          style={{ color: 'var(--text-primary)' }}
        >
          {t('webhooks.title')}
        </h1>
        <EmptyState message={t('errors.users.insufficient_permissions')} />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl">
      <div className="flex items-center justify-between mb-4">
        <h1
          className="text-xl font-semibold"
          style={{ color: 'var(--text-primary)' }}
        >
          {t('webhooks.title')}
        </h1>
        <button
          onClick={() => setShowCreate(s => !s)}
          className="px-3 py-1.5 rounded text-sm font-medium"
          style={{
            background: 'var(--io-accent)',
            color: 'var(--on-accent)',
          }}
        >
          {showCreate ? t('common.cancel') : t('webhooks.add_endpoint')}
        </button>
      </div>

      <p
        className="text-sm mb-4"
        style={{ color: 'var(--text-muted)' }}
      >
        {t('webhooks.intro')}
      </p>

      {feedback && (
        <div
          className="mb-3 p-3 rounded text-sm"
          style={{
            background: 'var(--accent-tint)',
            border: '1px solid var(--accent-border)',
            color: 'var(--text-primary)',
          }}
          role="status"
        >
          {feedback.message}
        </div>
      )}

      {error && <TranslatedError error={error} />}

      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="p-4 mb-6 rounded border"
          style={{
            background: 'var(--card-bg-solid)',
            borderColor: 'var(--card-border)',
            color: 'var(--text-primary)',
          }}
        >
          <div className="mb-3">
            <label
              className="block text-xs font-medium mb-1"
              style={{ color: 'var(--text-muted)' }}
            >
              {t('webhooks.form.name_label')}
            </label>
            <input
              type="text"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder={t('webhooks.form.name_placeholder')}
              className="w-full px-3 py-2 rounded text-sm"
              style={{
                background: 'var(--neutral-tint)',
                color: 'var(--text-primary)',
                border: '1px solid var(--card-border)',
              }}
            />
          </div>
          <div className="mb-3">
            <label
              className="block text-xs font-medium mb-1"
              style={{ color: 'var(--text-muted)' }}
            >
              {t('webhooks.form.url_label')}
            </label>
            <input
              type="url"
              required
              value={form.url}
              onChange={(e) => setForm({ ...form, url: e.target.value })}
              placeholder="https://example.com/webhook"
              className="w-full px-3 py-2 rounded text-sm"
              style={{
                background: 'var(--neutral-tint)',
                color: 'var(--text-primary)',
                border: '1px solid var(--card-border)',
              }}
            />
          </div>
          <div className="mb-3">
            <label
              className="block text-xs font-medium mb-1"
              style={{ color: 'var(--text-muted)' }}
            >
              {t('webhooks.form.event_types_label')}
            </label>
            <input
              type="text"
              value={form.event_types}
              onChange={(e) => setForm({ ...form, event_types: e.target.value })}
              placeholder="*"
              className="w-full px-3 py-2 rounded text-sm font-mono"
              style={{
                background: 'var(--neutral-tint)',
                color: 'var(--text-primary)',
                border: '1px solid var(--card-border)',
              }}
            />
            <p
              className="text-xs mt-1"
              style={{ color: 'var(--text-subtle)' }}
            >
              {t('webhooks.form.event_types_hint')}
            </p>
          </div>
          <button
            type="submit"
            className="px-4 py-2 rounded font-medium text-sm"
            style={{
              background: 'var(--io-accent)',
              color: 'var(--on-accent)',
            }}
          >
            {t('webhooks.form.submit')}
          </button>
        </form>
      )}

      {loading ? (
        <p style={{ color: 'var(--text-subtle)' }}>{t('common.loading')}</p>
      ) : endpoints.length === 0 ? (
        <EmptyState message={t('webhooks.empty')} />
      ) : (
        <div className="space-y-3">
          {endpoints.map((ep) => (
            <div
              key={ep.id}
              className="rounded border"
              style={{
                background: 'var(--card-bg-solid)',
                borderColor: 'var(--card-border)',
                color: 'var(--text-primary)',
              }}
            >
              <div className="p-4">
                {/* v1.0.0g-2: stack info above buttons on small screens,
                    side-by-side on sm+ (≥640px). Previously a single
                    flex-wrap row collapsed badly on narrow widths,
                    causing the URL to break per-character and buttons
                    to overlap the state pill. */}
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                  <div className="min-w-0 sm:flex-1 overflow-hidden">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <h3
                        className="font-medium truncate"
                        style={{ color: 'var(--text-primary)' }}
                        title={ep.name}
                      >
                        {ep.name}
                      </h3>
                      <StatePill state={ep.state} is_active={ep.is_active} t={t} />
                    </div>
                    {/* truncate (not break-all) + title for full URL
                        on hover. Avoids the one-character-per-line
                        collapse at extreme narrow widths. */}
                    <div
                      className="text-xs font-mono truncate mb-2"
                      style={{ color: 'var(--text-muted)' }}
                      title={ep.url}
                    >
                      {ep.url}
                    </div>
                    <div
                      className="text-xs"
                      style={{ color: 'var(--text-subtle)' }}
                    >
                      {ep.event_types?.length
                        ? ep.event_types.join(', ')
                        : '—'}
                    </div>
                    {ep.consecutive_failures > 0 && (
                      <div
                        className="text-xs mt-1"
                        style={{ color: 'var(--alert-burgundy)' }}
                      >
                        {t('webhooks.failure_count', {
                          n: ep.consecutive_failures,
                        })}
                      </div>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-1 sm:justify-end sm:flex-shrink-0">
                    <ActionBtn onClick={() => handleTest(ep)}>
                      {t('webhooks.action.test')}
                    </ActionBtn>
                    <ActionBtn onClick={() => handleToggleExpand(ep.id)}>
                      {expandedId === ep.id
                        ? t('webhooks.action.hide_deliveries')
                        : t('webhooks.action.show_deliveries')}
                    </ActionBtn>
                    <ActionBtn onClick={() => handleTogglePause(ep)}>
                      {ep.is_active
                        ? t('webhooks.action.pause')
                        : t('webhooks.action.resume')}
                    </ActionBtn>
                    {ep.state !== 'active' && (
                      <button
                        onClick={() => handleReenable(ep)}
                        className="px-2 py-1 rounded text-xs font-medium"
                        style={{
                          background: 'var(--io-accent)',
                          color: 'var(--on-accent)',
                        }}
                      >
                        {t('webhooks.action.reenable')}
                      </button>
                    )}
                    <ActionBtn onClick={() => handleRotate(ep)}>
                      {t('webhooks.action.rotate')}
                    </ActionBtn>
                    <button
                      onClick={() => handleDelete(ep)}
                      className="px-2 py-1 rounded text-xs font-medium"
                      style={{
                        background: 'var(--alert-burgundy)',
                        color: '#FFFFFF',
                      }}
                    >
                      {t('webhooks.action.delete')}
                    </button>
                  </div>
                </div>
              </div>
              {expandedId === ep.id && (
                <DeliveriesPanel
                  loading={loadingDeliveries}
                  deliveries={deliveries[ep.id] || []}
                  onRefresh={() => loadDeliveries(ep.id)}
                  t={t}
                />
              )}
            </div>
          ))}
        </div>
      )}

      {revealedSecret && (
        <WebhookSecretModal
          open={true}
          endpoint={revealedSecret}
          onAck={() => setRevealedSecret(null)}
        />
      )}
      <ConfirmOverlay />
    </div>
  );
}

function ActionBtn({ onClick, children }) {
  return (
    <button
      onClick={onClick}
      className="px-2 py-1 rounded text-xs font-medium"
      style={{
        background: 'var(--neutral-tint)',
        color: 'var(--text-primary)',
        border: '1px solid var(--card-border)',
      }}
    >
      {children}
    </button>
  );
}

function StatePill({ state, is_active, t }) {
  let bg, fg, label;
  if (!is_active) {
    bg = 'var(--neutral-tint)';
    fg = 'var(--text-muted)';
    label = t('webhooks.state.paused');
  } else if (state === 'active') {
    bg = 'var(--accent-tint)';
    fg = 'var(--io-accent)';
    label = t('webhooks.state.active');
  } else if (state === 'degraded') {
    bg = 'var(--pending-tint)';
    fg = 'var(--pending-color)';
    label = t('webhooks.state.degraded');
  } else if (state === 'disabled') {
    bg = 'var(--alert-tint)';
    fg = 'var(--alert-burgundy)';
    label = t('webhooks.state.disabled');
  } else {
    bg = 'var(--neutral-tint)';
    fg = 'var(--text-muted)';
    label = state;
  }
  return (
    <span
      className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider"
      style={{
        background: bg,
        color: fg,
        border: '1px solid currentColor',
      }}
    >
      {label}
    </span>
  );
}

function DeliveriesPanel({ loading, deliveries, onRefresh, t }) {
  return (
    <div
      className="border-t p-4"
      style={{
        background: 'var(--neutral-tint)',
        borderColor: 'var(--card-border)',
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <h4
          className="text-sm font-medium"
          style={{ color: 'var(--text-primary)' }}
        >
          {t('webhooks.deliveries.title')}
        </h4>
        <button
          onClick={onRefresh}
          className="text-xs font-medium"
          style={{ color: 'var(--io-accent)' }}
        >
          {t('common.refresh')}
        </button>
      </div>
      {loading ? (
        <p
          className="text-xs"
          style={{ color: 'var(--text-subtle)' }}
        >
          {t('common.loading')}
        </p>
      ) : deliveries.length === 0 ? (
        <p
          className="text-xs"
          style={{ color: 'var(--text-subtle)' }}
        >
          {t('webhooks.deliveries.empty')}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr style={{ color: 'var(--text-subtle)' }}>
                <th className="text-left py-1 pr-2">
                  {t('webhooks.deliveries.col.event_type')}
                </th>
                <th className="text-left py-1 pr-2">
                  {t('webhooks.deliveries.col.attempt')}
                </th>
                <th className="text-left py-1 pr-2">
                  {t('webhooks.deliveries.col.status')}
                </th>
                <th className="text-left py-1 pr-2">
                  {t('webhooks.deliveries.col.response')}
                </th>
                <th className="text-left py-1 pr-2">
                  {t('webhooks.deliveries.col.duration')}
                </th>
                <th className="text-left py-1">
                  {t('webhooks.deliveries.col.when')}
                </th>
              </tr>
            </thead>
            <tbody>
              {deliveries.map((d) => (
                <tr
                  key={d.id}
                  className="border-t"
                  style={{
                    borderColor: 'var(--card-border)',
                    color: 'var(--text-primary)',
                  }}
                >
                  <td className="py-1 pr-2 font-mono">{d.event_type}</td>
                  <td className="py-1 pr-2">{d.attempt}</td>
                  <td className="py-1 pr-2">
                    <DeliveryStatusPill status={d.status} />
                  </td>
                  <td className="py-1 pr-2">{d.response_status ?? '—'}</td>
                  <td className="py-1 pr-2">
                    {d.duration_ms != null ? `${d.duration_ms} ms` : '—'}
                  </td>
                  <td
                    className="py-1"
                    style={{ color: 'var(--text-subtle)' }}
                  >
                    {d.attempted_at
                      ? new Date(d.attempted_at).toLocaleString()
                      : new Date(d.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function DeliveryStatusPill({ status }) {
  let fg;
  if (status === 'success') fg = 'var(--io-accent)';
  else if (status === 'pending') fg = 'var(--pending-color)';
  else if (status === 'failed' || status === 'exhausted')
    fg = 'var(--alert-burgundy)';
  else fg = 'var(--text-muted)';
  return (
    <span
      className="font-semibold uppercase tracking-wider text-[10px]"
      style={{ color: fg }}
    >
      {status}
    </span>
  );
}
