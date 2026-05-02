/**
 * useEventStream — subscribe to a server-side event stream (SSE).
 *
 * v1.0-pre #8/#9: opens an EventSource against the backend's
 * /api/events/{id}/<surface>/stream endpoint. Calls onEvent(message)
 * for each parsed message. Auto-reconnects on connection loss with
 * exponential backoff. Closes cleanly on unmount.
 *
 * Why a custom hook rather than just `new EventSource(...)`? Three
 * things the raw API doesn't give you:
 *   1. JWT auth via ?token=... query — EventSource can't add headers,
 *      so the backend's get_current_user_query_token reads the token
 *      from the URL. We don't want every callsite re-implementing that.
 *   2. Backoff on disconnect — the browser's auto-reconnect uses a
 *      fixed 3s delay. For mobile-network drops we want 0.5/1/2/4/8s.
 *   3. Pause when the tab is hidden — saves both the client and the
 *      server queue when nobody's watching.
 *
 * Usage:
 *   useEventStream({
 *     eventId,
 *     surface: 'checkin',
 *     onEvent: (msg) => { ... },
 *     enabled: true,  // optional, default true
 *   });
 */

import { useEffect, useRef } from 'react';
import { getToken } from '../services/api';

export function useEventStream({ eventId, surface, onEvent, enabled = true }) {
  // useRef so the callback can be swapped on each render without
  // tearing down the EventSource.
  const onEventRef = useRef(onEvent);
  useEffect(() => { onEventRef.current = onEvent; }, [onEvent]);

  useEffect(() => {
    if (!enabled || !eventId || !surface) return;

    let es = null;
    let backoffMs = 500;
    let reconnectTimer = null;
    let cancelled = false;

    const connect = () => {
      if (cancelled) return;
      const token = getToken();
      if (!token) {
        // No auth — nothing to do. Will retry when token comes back.
        reconnectTimer = setTimeout(connect, 2000);
        return;
      }
      const url = `/api/events/${eventId}/${surface}/stream?token=${encodeURIComponent(token)}`;
      es = new EventSource(url);

      es.onopen = () => {
        backoffMs = 500; // reset backoff on successful connection
      };

      // The server emits typed events (event: <type>\n data: <json>).
      // EventSource fires these as named events on the source. We
      // listen via addEventListener so we catch any type the server
      // chooses to emit, not just the default 'message'.
      const onAnyEvent = (e) => {
        if (cancelled) return;
        try {
          const data = e.data ? JSON.parse(e.data) : null;
          if (data && onEventRef.current) {
            // Pass through both the message body and the SSE event type
            // so consumers can switch on `type` without re-parsing.
            onEventRef.current({ ...data, type: data.type || e.type });
          }
        } catch (_err) {
          // Malformed payload — skip silently. Heartbeat lines (":")
          // never reach here; they're consumed by the protocol layer.
        }
      };

      // Listen for the named event types the backend emits. New ones
      // can be added here without breaking existing consumers.
      ['connected', 'checkin_changed', 'checkin_value_changed',
       'allocation_changed', 'message'].forEach(t => {
        es.addEventListener(t, onAnyEvent);
      });

      es.onerror = () => {
        // Connection lost or refused. Close and schedule reconnect
        // with backoff. EventSource's built-in reconnect is too
        // aggressive (no backoff on repeated failures).
        if (es) {
          es.close();
          es = null;
        }
        if (cancelled) return;
        reconnectTimer = setTimeout(connect, backoffMs);
        backoffMs = Math.min(backoffMs * 2, 16000);
      };
    };

    connect();

    // Pause the stream while the tab is hidden — saves backend queue
    // pressure and avoids stale state buildup. Reconnect on focus.
    const onVisibility = () => {
      if (document.visibilityState === 'hidden') {
        if (es) { es.close(); es = null; }
      } else if (!es && !cancelled) {
        backoffMs = 500;
        connect();
      }
    };
    document.addEventListener('visibilitychange', onVisibility);

    return () => {
      cancelled = true;
      document.removeEventListener('visibilitychange', onVisibility);
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (es) es.close();
    };
  }, [eventId, surface, enabled]);
}
