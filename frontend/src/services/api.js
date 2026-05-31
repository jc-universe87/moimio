/**
 * Moimio API client — all backend communication goes through here.
 */

const API_BASE = '/api';

let accessToken = null;

export function setToken(token) { accessToken = token; }
export function getToken() { return accessToken; }
export function clearToken() { accessToken = null; }

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`;
  // v0.70d-2b (R6): errors thrown by request() now carry .status and
  // .isNetwork so callers can distinguish HTTP error responses (bad
  // creds, 500, etc.) from true network failures (fetch rejected,
  // server unreachable). The .message string is unchanged so existing
  // consumers that only inspect .message keep working.
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch (err) {
    // `fetch` only rejects for network-level failures (DNS, connection
    // refused, CORS pre-flight failure, client offline, abort). HTTP
    // error statuses are resolved responses, handled below.
    const netErr = new Error(err?.message || 'Network request failed');
    netErr.isNetwork = true;
    netErr.status = 0;
    netErr.cause = err;
    // v0.70d-3b (M5): friendlyKey for the categories layer — the
    // formatErrorMessage() helper consumes this to render a friendly
    // primary line above the raw message detail.
    netErr.friendlyKey = 'errors.network';
    throw netErr;
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    // v0.70d-3b (M5 Approach 4): backend may send a structured detail
    // of the shape { key, params } for translatable error messages on
    // converted endpoints. Frontend extracts the key and params here;
    // formatErrorMessage() resolves the key via t() at render time.
    // Plain-string detail (legacy / unconverted endpoints) keeps
    // working unchanged — message is the string, no i18nKey set.
    let message;
    let i18nKey = null;
    let i18nParams = null;
    if (data?.detail && typeof data.detail === 'object' && !Array.isArray(data.detail) && typeof data.detail.key === 'string') {
      i18nKey = data.detail.key;
      i18nParams = data.detail.params || null;
      // Legacy fallback: message stays human-readable in EN even if
      // t() can't resolve the key. Use the params dict as a coarse
      // fallback summary.
      message = `[${i18nKey}]`;
    } else {
      message = data?.detail || `Request failed (${res.status})`;
    }
    const httpErr = new Error(typeof message === 'string' ? message : JSON.stringify(message));
    httpErr.status = res.status;
    if (i18nKey) {
      httpErr.i18nKey = i18nKey;
      if (i18nParams) httpErr.i18nParams = i18nParams;
    }
    // v0.70d-2d-1 (L1): 502 / 503 / 504 are upstream-gone scenarios —
    // the proxy reached us but the backend container is down or
    // overloaded. These look like HTTP responses to fetch() but are
    // structurally network failures. Classify them as such so callers
    // route to "couldn't reach server" UI rather than "bad credentials"
    // or "data error" buckets. Fixes the auth case where stopping the
    // backend produced a misleading "Invalid email or password" banner;
    // also silently improves every other surface that branches on
    // .isNetwork.
    httpErr.isNetwork = res.status === 502 || res.status === 503 || res.status === 504;
    // v0.70d-3b (M5 Approach 3): map status to a friendly category
    // key. Helper formatErrorMessage() resolves this for display so
    // the user sees a human framing first, with the raw detail
    // available below as supplementary text.
    if (httpErr.isNetwork) {
      httpErr.friendlyKey = 'errors.network';
    } else if (res.status === 401) {
      httpErr.friendlyKey = 'errors.unauthorised';
    } else if (res.status === 403) {
      httpErr.friendlyKey = 'errors.forbidden';
    } else if (res.status === 404) {
      httpErr.friendlyKey = 'errors.not_found';
    } else if (res.status === 409) {
      httpErr.friendlyKey = 'errors.conflict';
    } else if (res.status === 422) {
      httpErr.friendlyKey = 'errors.validation';
    } else if (res.status >= 500) {
      httpErr.friendlyKey = 'errors.server';
    }
    throw httpErr;
  }
  return data;
}

// v0.70d-3b (M5): structured error formatter. Returns
// { primary, detail } where:
//   - primary: friendly translated string for display as the top line
//     (resolved from err.i18nKey if present, else from err.friendlyKey
//     category, else falls back to err.message)
//   - detail: the original backend message string, or null if it was
//     synthesised (e.g. network-failure message) and adds no value
//
// Callers render `primary` boldly and `detail` (when non-null) as a
// muted secondary line. ErrorBanner-using callsites can adopt this
// incrementally — existing ones that just render err.message keep
// working unchanged.
//
// Accepts either an Error object (preferred — gives full structured
// access) or a plain string (legacy callsites that already extracted
// err.message). String input falls back to {primary: input, detail: null}.
//
// Usage:
//   const { primary, detail } = formatErrorMessage(err, t);
//   <ErrorBanner>
//     <p className="font-semibold">{primary}</p>
//     {detail && <p className="text-xs opacity-70 mt-1">{detail}</p>}
//   </ErrorBanner>
export function formatErrorMessage(err, t) {
  if (!err) return { primary: '', detail: null };

  // Legacy callsites store `err.message` directly as a string. Render
  // it bare with no detail line.
  if (typeof err === 'string') {
    return { primary: err, detail: null };
  }

  // Approach-1 / Approach-4 path: backend sent a translatable key
  if (err.i18nKey) {
    const translated = t(err.i18nKey, err.i18nParams || {});
    // v0.70d-3c-8: t() returns `[key]` when the key is missing in
    // both the active locale AND the EN fallback. Treat that case as
    // a miss too — falling through to friendlyKey produces a generic
    // translated category line instead of leaking the bracketed key
    // into the UI.
    const isBracketedFallback = translated === `[${err.i18nKey}]`;
    if (translated !== err.i18nKey && !isBracketedFallback) {
      return { primary: translated, detail: null };
    }
  }

  // Approach-3 categories path: friendly category from status
  if (err.friendlyKey) {
    const category = t(err.friendlyKey);
    // For network failures, the raw err.message ("Failed to fetch"
    // / "Network request failed") adds no user value — suppress.
    const isSyntheticNetworkMessage = err.isNetwork || err.status === 0;
    return {
      primary: category,
      detail: isSyntheticNetworkMessage ? null : (err.message || null),
    };
  }

  // No friendlyKey set (very rare path — request() always sets one
  // for non-2xx) — fall back to bare message.
  return { primary: err.message || '', detail: null };
}

// ─── Auth ───
export const auth = {
  login: (email, password) => request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  me: () => request('/auth/me'),
  logout: () => request('/auth/logout', { method: 'POST' }),
  // v0.99b audit: changePassword previously used PUT, but the backend
  // declares PATCH /api/auth/me/password (auth.py:150). The mismatch
  // would have produced 405 Method Not Allowed if anyone called it.
  // No UI currently invokes this method.
  changePassword: (current_password, new_password) =>
    request('/auth/me/password', { method: 'PATCH', body: JSON.stringify({ current_password, new_password }) }),
  createUser: (data) => request('/auth/users', { method: 'POST', body: JSON.stringify(data) }),
  // v0.99b audit: listUsers previously called GET /api/auth/users, but
  // no such route exists — the only GET endpoint for listing users is
  // GET /api/users/ in users.py. The proper user-management UI uses
  // usersApi.list (api.js line ~352) which already hits the right
  // endpoint. This shorthand is preserved for any future caller.
  listUsers: () => request('/users/'),
};

// ─── Events ───
export const events = {
  list: () => request('/events/'),
  get: (id) => request(`/events/${id}`),
  getPublic: (id) => request(`/events/${id}/public`),
  create: (data) => request('/events/', { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`/events/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  getFields: (eventId) => request(`/events/${eventId}/fields`),
  setFields: (eventId, configs) => request(`/events/${eventId}/fields`, { method: 'PUT', body: JSON.stringify(configs) }),
  getFieldsPublic: (eventId) => request(`/events/${eventId}/fields/public`),
  // Setup hub (v50b §3 gate rules).
  // `card` is 'details' or 'registration'. The server silently unconfirms
  // either flag whenever the underlying data is edited during Setup phase.
  confirmCard: (eventId, card) =>
    request(`/events/${eventId}/setup/confirm/${card}`, { method: 'POST' }),
  unconfirmCard: (eventId, card) =>
    request(`/events/${eventId}/setup/unconfirm/${card}`, { method: 'POST' }),
  openRegistration: (eventId) =>
    request(`/events/${eventId}/registration/open`, { method: 'POST' }),
  closeRegistration: (eventId) =>
    request(`/events/${eventId}/registration/close`, { method: 'POST' }),
  // v0.50g-2: aggregate stats for the Reports page.
  stats: (eventId) => request(`/events/${eventId}/stats`),
  // v0.50g-2: hard-delete an event (Super Admin only). Returns void on 204.
  // v1.0.0h-1: now also emits an event.deleted webhook server-side
  // (handled in the delete_event service, same DB transaction). On a
  // paid SaaS plan the receiver applies its own 24-hour refund policy;
  // CE simply tells SaaS the deletion happened.
  delete: (eventId) => request(`/events/${eventId}`, { method: 'DELETE' }),
  // v0.50i: archive/unarchive (Super Admin only). Archived events are
  // read-only to everyone except Super Admin and hidden from the
  // default events-list groupings.
  archive: (eventId) => request(`/events/${eventId}/archive`, { method: 'POST' }),
  unarchive: (eventId) => request(`/events/${eventId}/unarchive`, { method: 'POST' }),
  // v0.51: duplicate preview counts. Small response used by DuplicateEventPage
  // to show "Will also copy: N marks, N form fields, …". Caller must have
  // access to the source event (Super Admin OR assigned via EventUserAssignment).
  duplicateCounts: (eventId) => request(`/events/${eventId}/duplicate/counts`),
};

// ─── Participants ───
export const participants = {
  list: (eventId) => request(`/events/${eventId}/participants`),
  get: (id) => request(`/participants/${id}`),
  register: (eventId, data) => request(`/events/${eventId}/register`, { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`/participants/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  checkin: (id, checked_in) => request(`/participants/${id}/checkin`, { method: 'POST', body: JSON.stringify({ checked_in }) }),
  delete: (id) => request(`/participants/${id}`, { method: 'DELETE' }),
};

// ─── Allocation Categories ───
export const allocationCategories = {
  list: (eventId) => request(`/events/${eventId}/allocation-categories/`),
  create: (eventId, data) => request(`/events/${eventId}/allocation-categories/`, { method: 'POST', body: JSON.stringify(data) }),
  update: (eventId, catId, data) => request(`/events/${eventId}/allocation-categories/${catId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (eventId, catId) => request(`/events/${eventId}/allocation-categories/${catId}`, { method: 'DELETE' }),
  reorder: (eventId, orderedIds) => request(`/events/${eventId}/allocation-categories/reorder`, { method: 'POST', body: JSON.stringify({ ordered_ids: orderedIds }) }),
  reorderUnits: (eventId, catId, orderedIds) => request(`/events/${eventId}/allocation-categories/${catId}/units/reorder`, { method: 'POST', body: JSON.stringify({ ordered_ids: orderedIds }) }),
  suggest: (eventId, catId, mode = 'replace') => request(`/events/${eventId}/allocation-categories/${catId}/suggest?mode=${mode}`, { method: 'POST' }),
  // v0.60c: commit now forwards the engine's reasoning payload so the
  // backend can write it into each assign event's meta JSONB. Callers
  // with only `proposed` continue to work — the extras default to
  // null server-side and meta stays None.
  commit: (eventId, catId, proposed, { placementReasons, engineRunId } = {}) => request(
    `/events/${eventId}/allocation-categories/${catId}/commit`,
    {
      method: 'POST',
      body: JSON.stringify({
        proposed,
        placement_reasons: placementReasons ?? null,
        engine_run_id: engineRunId ?? null,
      }),
    },
  ),
  clear: (eventId, catId) => request(`/events/${eventId}/allocation-categories/${catId}/clear`, { method: 'POST' }),
  // v50c-3: allocation lifecycle confirm/unconfirm
  confirm:   (eventId, catId) => request(`/events/${eventId}/allocation-categories/${catId}/confirm`,   { method: 'POST' }),
  unconfirm: (eventId, catId) => request(`/events/${eventId}/allocation-categories/${catId}/unconfirm`, { method: 'POST' }),
};

// ─── Allocation Units ───
export const allocationUnits = {
  list: (eventId, catId) => request(`/events/${eventId}/allocation-categories/${catId}/units/`),
  create: (eventId, catId, data) => request(`/events/${eventId}/allocation-categories/${catId}/units/`, { method: 'POST', body: JSON.stringify(data) }),
  update: (eventId, catId, unitId, data) => request(`/events/${eventId}/allocation-categories/${catId}/units/${unitId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (eventId, catId, unitId) => request(`/events/${eventId}/allocation-categories/${catId}/units/${unitId}`, { method: 'DELETE' }),
};

// ─── Allocations (core actions) ───
export const allocations = {
  assign: (eventId, participantId, unitId) =>
    request(`/events/${eventId}/allocations/assign`, { method: 'POST', body: JSON.stringify({ participant_id: participantId, unit_id: unitId }) }),
  move: (eventId, participantId, toUnitId) =>
    request(`/events/${eventId}/allocations/move`, { method: 'POST', body: JSON.stringify({ participant_id: participantId, to_unit_id: toUnitId }) }),
  unassign: (eventId, unitId, participantId) =>
    request(`/events/${eventId}/allocations/unassign/${unitId}/${participantId}`, { method: 'DELETE' }),
  byCategory: (eventId, catId) => request(`/events/${eventId}/allocations/by-category/${catId}`),
  all: (eventId) => request(`/events/${eventId}/allocations/all`),
};

// ─── Allocation events (audit log read; v0.60b) ───
// Admin-only. Returns rows newest-first. See backend
// allocation_events_service.list_allocation_events for shape.
export const allocationEvents = {
  list: (eventId, { participantId, limit } = {}) => {
    const qs = new URLSearchParams();
    if (participantId) qs.set('participant_id', participantId);
    if (limit) qs.set('limit', String(limit));
    const suffix = qs.toString() ? `?${qs}` : '';
    return request(`/events/${eventId}/allocation-events${suffix}`);
  },
};

// ─── Custom Fields ───
export const customFields = {
  list: (eventId) => request(`/events/${eventId}/custom-fields/`),
  create: (eventId, data) => request(`/events/${eventId}/custom-fields/`, { method: 'POST', body: JSON.stringify(data) }),
  update: (eventId, fieldId, data) => request(`/events/${eventId}/custom-fields/${fieldId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (eventId, fieldId) => request(`/events/${eventId}/custom-fields/${fieldId}`, { method: 'DELETE' }),
};

// ─── Preference Requests ───
export const preferenceRequests = {
  list: (eventId) => request(`/events/${eventId}/preference-requests/`),
  resolve: (eventId, reqId, data) => request(`/events/${eventId}/preference-requests/${reqId}/resolve`, { method: 'PATCH', body: JSON.stringify(data) }),
};

// ─── Notes ───
export const notes = {
  list: (notableType, notableId) => request(`/notes/?notable_type=${notableType}&notable_id=${notableId}`),
  create: (data) => request('/notes/', { method: 'POST', body: JSON.stringify(data) }),
  delete: (noteId) => request(`/notes/${noteId}`, { method: 'DELETE' }),
  counts: (eventId) => request(`/notes/counts?event_id=${eventId}`),
};

// ─── Preferences ───
export const preferences = {
  get: () => request('/auth/me/preferences/'),
  update: (data) => request('/auth/me/preferences/', { method: 'PATCH', body: JSON.stringify(data) }),
};

// ─── Email ───
export const email = {
  test: (eventId) => request(`/events/${eventId}/test-email`, { method: 'POST' }),
};

// ─── Check-in ───
export const checkin = {
  listFields: (eventId) => request(`/events/${eventId}/checkin-fields/`),
  createField: (eventId, data) => request(`/events/${eventId}/checkin-fields/`, { method: 'POST', body: JSON.stringify(data) }),
  deleteField: (eventId, fieldId) => request(`/events/${eventId}/checkin-fields/${fieldId}`, { method: 'DELETE' }),
  getValues: (eventId) => request(`/events/${eventId}/checkin-values/`),
  toggleValue: (eventId, participantId, fieldId, checked) =>
    request(`/events/${eventId}/checkin-values/`, { method: 'POST', body: JSON.stringify({ participant_id: participantId, field_id: fieldId, checked }) }),
};

// ─── Marks ───
export const marks = {
  listDefs: (eventId) => request(`/events/${eventId}/marks/`),
  createDef: (eventId, data) => request(`/events/${eventId}/marks/`, { method: 'POST', body: JSON.stringify(data) }),
  updateDef: (eventId, markId, data) => request(`/events/${eventId}/marks/${markId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteDef: (eventId, markId) => request(`/events/${eventId}/marks/${markId}`, { method: 'DELETE' }),
  importFrom: (eventId, sourceEventId) => request(`/events/${eventId}/marks/import`, { method: 'POST', body: JSON.stringify({ source_event_id: sourceEventId }) }),
  listAssignments: (eventId) => request(`/events/${eventId}/marks/assignments`),
  assign: (eventId, markId, participantId) => request(`/events/${eventId}/marks/${markId}/assign`, { method: 'POST', body: JSON.stringify({ participant_id: participantId }) }),
  unassign: (eventId, markId, participantId) => request(`/events/${eventId}/marks/${markId}/assign/${participantId}`, { method: 'DELETE' }),
};

// ─── Password Reset ───
export const passwordReset = {
  request: (email) => request('/auth/request-reset', { method: 'POST', body: JSON.stringify({ email }) }),
  confirm: (token, new_password) => request('/auth/reset-password', { method: 'POST', body: JSON.stringify({ token, new_password }) }),
};

// ─── Setup ───
export const setup = {
  status: () => request('/setup/status'),
  init: (data) => request('/setup/init', { method: 'POST', body: JSON.stringify(data) }),
};

// ─── User Management ───
export const users = {
  list: () => request('/users/'),
  create: (data) => request('/users/', { method: 'POST', body: JSON.stringify(data) }),
  update: (userId, data) => request(`/users/${userId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (userId) => request(`/users/${userId}`, { method: 'DELETE' }),
};

// ─── Event Assignments ───
// v0.50e-1b: permissions are now part of each assignment's body (no more
// shared staff groups). Create/update accept { user_id, role, permissions }.
// v0.50e-1c: myEvents returns the full list of assignments for the current
// user. myEvent kept as back-compat shim; new code should use myEvents.
export const eventAssignments = {
  list: (eventId) => request(`/events/${eventId}/assignments/`),
  create: (eventId, data) => request(`/events/${eventId}/assignments/`, { method: 'POST', body: JSON.stringify(data) }),
  update: (eventId, assignmentId, data) => request(`/events/${eventId}/assignments/${assignmentId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (eventId, assignmentId) => request(`/events/${eventId}/assignments/${assignmentId}`, { method: 'DELETE' }),
  myEvents: () => request('/my-events'),
  myEvent: () => request('/my-event'),  // back-compat, deprecated
};

// ─── Capabilities (v1.0.0g) ───
// Frontend reads this once on boot (in App.jsx / I18nProvider boot path)
// to know which features the instance has enabled. Used to gate sidebar
// nav entries and feature surfaces. Public endpoint — no auth required.
export const capabilities = {
  get: () => request('/capabilities'),
};

// ─── Billing info (v1.0.0h) ───
// Returns the per-tenant amount/currency/card-last-4 used by the
// create-event confirmation dialog. Only call this when
// capabilities.create_event_confirmation is true — for self-hosters
// and tenants where the flag is off, this data is not relevant.
// Auth required; the card last-4 is customer data.
export const billingInfo = {
  get: () => request('/billing-info'),
};

// ─── Outbound webhooks (v1.0.0g) ───
// Admin-only CRUD for outbound webhook endpoints + delivery log.
// The CREATE and ROTATE responses include a plaintext `secret` field
// exactly once; consumers must capture and display it via the sticky
// "show once" modal pattern. GET responses never include the secret.
export const outboundWebhooks = {
  list: () => request('/webhooks/endpoints'),
  get: (id) => request(`/webhooks/endpoints/${id}`),
  create: (data) => request('/webhooks/endpoints', { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`/webhooks/endpoints/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id) => request(`/webhooks/endpoints/${id}`, { method: 'DELETE' }),
  rotateSecret: (id) => request(`/webhooks/endpoints/${id}/rotate-secret`, { method: 'POST' }),
  reenable: (id) => request(`/webhooks/endpoints/${id}/reenable`, { method: 'POST' }),
  sendTest: (id) => request(`/webhooks/endpoints/${id}/test`, { method: 'POST' }),
  listDeliveries: (id, limit = 50) => request(`/webhooks/endpoints/${id}/deliveries?limit=${limit}`),
};

// ─── Danger Zone — workspace-level destructive actions (v1.0.0v) ───
// Backed by /api/admin/workspace/* on the backend; super-admin only.
// The confirmation token is the canonical English literal "DELETE"
// regardless of UI locale (the modal lets the user type it; the
// frontend normalises case before submitting).
export const dangerZone = {
  requestDeletion: (confirmation) => request('/admin/workspace/request-deletion', {
    method: 'POST',
    body: JSON.stringify({ confirmation }),
  }),
};
