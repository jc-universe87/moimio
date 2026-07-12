import { createContext, useContext, useState, useEffect } from 'react';
import { capabilities as capabilitiesApi } from '../services/api';

/**
 * useCapabilities — v1.0.0g.
 *
 * Reads /api/capabilities once on mount and exposes the capability flags
 * to any component that needs to gate UI on them (allocation engine,
 * outbound webhooks admin section, etc.).
 *
 * Default while loading: all capabilities OPTIMISTICALLY ON. The
 * rationale: in a healthy deployment all flags are on; transient
 * loading flicker should not blank out the sidebar. If the endpoint
 * fails we keep optimistic defaults so the UI stays functional — at
 * worst a user sees a nav entry that 404s when clicked, which is a
 * better failure mode than a blank sidebar.
 *
 * Capabilities don't change without a container restart, so we never
 * refetch. One read at mount is sufficient.
 */

const DEFAULT_CAPABILITIES = {
  allocation: true,
  outbound_webhooks: true,
  // v1.0.0h-2: default to OFF for this one specifically. Optimistic-on
  // defaults are right for capabilities the UI gates *features* on
  // (showing a sidebar entry that 404s is less bad than blanking out
  // the sidebar). But this flag gates inserting an extra confirmation
  // dialog into the event-create flow — showing a "you'll be charged"
  // dialog to a self-hoster on a transient capability-fetch failure
  // would be confusing and wrong. Off-by-default fails closed: a real
  // SaaS tenant just doesn't see the dialog on a flicker, which is
  // recoverable; a self-hoster never sees it spuriously.
  create_event_confirmation: false,
  // v1.0.0aa: SaaS account-portal URL. Empty by default — like
  // create_event_confirmation, a missing/failed fetch must NOT surface a
  // hosted-only link. A self-hoster (or a transient capabilities failure)
  // keeps the empty default and the "Manage account" link stays hidden; a
  // real tenant just doesn't see it until the next load. Fail-closed.
  account_url: '',
  // v1.0.2c: the managed-instance signal (v1.0.1e-6 added the backend
  // field and the AdminLayout gates, but this provider never mapped it —
  // so capabilities.account_portal was undefined forever and the gates
  // were dead). Fail-closed like the two flags above: hosted-only UI
  // must never flash for a self-hoster on a fetch flicker.
  account_portal: false,
};

const CapabilitiesContext = createContext({
  capabilities: DEFAULT_CAPABILITIES,
  loading: false,
});

export function CapabilitiesProvider({ children }) {
  const [caps, setCaps] = useState(DEFAULT_CAPABILITIES);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    capabilitiesApi.get()
      .then(data => {
        if (!cancelled && data && typeof data === 'object') {
          setCaps({
            allocation: data.allocation !== false,
            outbound_webhooks: data.outbound_webhooks !== false,
            // v1.0.0h-2: explicitly false unless the API says true. The
            // !== false trick we use for the legacy flags is wrong here
            // because it would interpret a missing field as "on" rather
            // than "off" — and missing-means-off is the right default
            // for a flag added in a later version.
            create_event_confirmation: data.create_event_confirmation === true,
            // v1.0.0aa: string passthrough; anything non-string (missing,
            // null) becomes '' so the link stays hidden. Same fail-closed
            // intent as create_event_confirmation above.
            account_url: typeof data.account_url === 'string' ? data.account_url : '',
            // v1.0.2c: same missing-means-off pattern as
            // create_event_confirmation — this line was the missing half
            // of the e-6 feature (see DEFAULT_CAPABILITIES note).
            account_portal: data.account_portal === true,
          });
        }
      })
      .catch(() => {
        // Keep optimistic defaults on failure — see rationale above.
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  return (
    <CapabilitiesContext.Provider value={{ capabilities: caps, loading }}>
      {children}
    </CapabilitiesContext.Provider>
  );
}

export function useCapabilities() {
  return useContext(CapabilitiesContext);
}
