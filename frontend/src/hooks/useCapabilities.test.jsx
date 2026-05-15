/**
 * useCapabilities — regression-pin tests (v1.0.0h-3).
 *
 * The bug these tests would have caught: in v1.0.0h I added a new
 * `create_event_confirmation` field to the /api/capabilities response,
 * but forgot to update this hook to read it. The hook destructures
 * specific fields rather than spreading the whole response, so the
 * new field was silently dropped. Frontend got back capabilities
 * with the field permanently missing, and the create-confirm dialog
 * never appeared. Pure backend tests passed; only a real-device
 * smoke test surfaced the issue.
 *
 * These tests pin the contract: when the API returns a field, the
 * hook MUST expose it on the capabilities object. If you add a
 * new capability to the API in future, add a test here at the
 * same time. The regression cost of forgetting is non-trivial:
 * it ships, looks fine to backend, and only the user sees it.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

// Mock the api module BEFORE importing the hook (Vitest hoists vi.mock).
// This lets each test pose as the backend returning whatever response shape
// we want to verify against.
vi.mock('../services/api', () => ({
  capabilities: {
    get: vi.fn(),
  },
}));

import { CapabilitiesProvider, useCapabilities } from './useCapabilities';
import { capabilities as capabilitiesApi } from '../services/api';

/**
 * Tiny consumer component that just renders the hook's value as JSON.
 * Lets tests assert against the rendered text rather than mocking
 * useContext directly (which would defeat the point of testing
 * through the Provider).
 */
function HookProbe() {
  const { capabilities, loading } = useCapabilities();
  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="caps">{JSON.stringify(capabilities)}</span>
    </div>
  );
}

describe('useCapabilities', () => {
  beforeEach(() => {
    capabilitiesApi.get.mockReset();
  });

  it('exposes create_event_confirmation when the API returns it as true', async () => {
    // THIS IS THE REGRESSION-PIN TEST. The v1.0.0h bug was that
    // useCapabilities dropped this field on the floor. If this test
    // passes, the bug cannot recur silently.
    capabilitiesApi.get.mockResolvedValue({
      allocation: true,
      outbound_webhooks: true,
      create_event_confirmation: true,
    });

    render(
      <CapabilitiesProvider>
        <HookProbe />
      </CapabilitiesProvider>,
    );

    await waitFor(() => {
      const caps = JSON.parse(screen.getByTestId('caps').textContent);
      expect(caps.create_event_confirmation).toBe(true);
    });
  });

  it('exposes create_event_confirmation as false when API returns it false', async () => {
    capabilitiesApi.get.mockResolvedValue({
      allocation: true,
      outbound_webhooks: true,
      create_event_confirmation: false,
    });

    render(
      <CapabilitiesProvider>
        <HookProbe />
      </CapabilitiesProvider>,
    );

    await waitFor(() => {
      const caps = JSON.parse(screen.getByTestId('caps').textContent);
      expect(caps.create_event_confirmation).toBe(false);
    });
  });

  it('defaults create_event_confirmation to false when API omits it', async () => {
    // A pre-v1.0.0h backend (or any backend that drops the field) MUST
    // be treated as "off" by the frontend. Showing a "you'll be charged"
    // dialog to a self-hoster on a transient API failure or version
    // mismatch would be the wrong failure mode.
    capabilitiesApi.get.mockResolvedValue({
      allocation: true,
      outbound_webhooks: true,
      // create_event_confirmation intentionally absent
    });

    render(
      <CapabilitiesProvider>
        <HookProbe />
      </CapabilitiesProvider>,
    );

    await waitFor(() => {
      const caps = JSON.parse(screen.getByTestId('caps').textContent);
      expect(caps.create_event_confirmation).toBe(false);
    });
  });

  it('defaults create_event_confirmation to false when API fetch fails', async () => {
    // Catch-clause path. Same fail-closed logic as the omitted-field case.
    capabilitiesApi.get.mockRejectedValue(new Error('network'));

    render(
      <CapabilitiesProvider>
        <HookProbe />
      </CapabilitiesProvider>,
    );

    await waitFor(() => {
      // Loading flips to false in finally{} even on failure.
      expect(screen.getByTestId('loading').textContent).toBe('false');
    });
    const caps = JSON.parse(screen.getByTestId('caps').textContent);
    expect(caps.create_event_confirmation).toBe(false);
  });

  it('preserves allocation and outbound_webhooks fields', async () => {
    // Regression-pin for the legacy fields too. If a future refactor
    // breaks the hook's destructuring, the legacy gates should fail
    // loudly here rather than silently shipping with all sidebar
    // entries hidden.
    capabilitiesApi.get.mockResolvedValue({
      allocation: false,
      outbound_webhooks: true,
      create_event_confirmation: false,
    });

    render(
      <CapabilitiesProvider>
        <HookProbe />
      </CapabilitiesProvider>,
    );

    await waitFor(() => {
      const caps = JSON.parse(screen.getByTestId('caps').textContent);
      expect(caps.allocation).toBe(false);
      expect(caps.outbound_webhooks).toBe(true);
    });
  });

  it('uses optimistic defaults during the initial fetch', () => {
    // Before the API responds, the consumer sees the defaults — which
    // are deliberately tuned: optimistic-on for capabilities that
    // gate sidebar entries (better than blanking), off for the
    // charge-confirmation flag (don't show billing dialogs on a
    // pre-fetch render).
    capabilitiesApi.get.mockReturnValue(new Promise(() => { /* never resolves */ }));

    render(
      <CapabilitiesProvider>
        <HookProbe />
      </CapabilitiesProvider>,
    );

    const caps = JSON.parse(screen.getByTestId('caps').textContent);
    expect(caps.allocation).toBe(true);
    expect(caps.outbound_webhooks).toBe(true);
    expect(caps.create_event_confirmation).toBe(false);
    expect(screen.getByTestId('loading').textContent).toBe('true');
  });
});
