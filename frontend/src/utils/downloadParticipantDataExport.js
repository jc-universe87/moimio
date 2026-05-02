/**
 * downloadParticipantDataExport — fetch a participant's DSAR export
 * and trigger a browser download. v0.73.
 *
 * Wraps the inline-fetch+blob pattern that's used elsewhere in the
 * codebase (e.g. BatchRegisterModal's CSV template download). Both
 * trigger surfaces (InsightPanel, PeopleTable) call this so the
 * download mechanics live in one place.
 *
 * The endpoint sets Content-Disposition with the canonical filename
 * (`participant-export-{number-or-uuid8}-{date}.json`); we extract
 * it from the response header rather than reconstructing client-side.
 * If the header is missing or malformed, fall back to a sensible
 * default. Returns nothing on success; throws on failure so the
 * caller can surface a toast or other UI.
 *
 * The thrown error carries the same `.status` / `.i18nKey` /
 * `.friendlyKey` shape as request() in services/api.js, so callers
 * can pass it straight to formatErrorMessage(err, t).
 *
 * @param {Object} args
 * @param {string} args.eventId
 * @param {string} args.participantId
 * @param {string} args.token       Bearer token (from getToken()).
 * @returns {Promise<void>}         Resolves when the download has
 *                                  been triggered. Does not wait for
 *                                  the user to confirm the save.
 * @throws {Error} On HTTP error or network failure. Error has:
 *                 - .status     (HTTP status, 0 for network)
 *                 - .isNetwork  (boolean)
 *                 - .i18nKey    (when backend sent a structured detail)
 *                 - .friendlyKey (categories layer for formatErrorMessage)
 */
export async function downloadParticipantDataExport({ eventId, participantId, token }) {
  let res;
  try {
    res = await fetch(
      `/api/events/${eventId}/participants/${participantId}/data-export`,
      { headers: { Authorization: `Bearer ${token || ''}` } }
    );
  } catch (err) {
    const netErr = new Error(err?.message || 'Network request failed');
    netErr.isNetwork = true;
    netErr.status = 0;
    netErr.cause = err;
    netErr.friendlyKey = 'errors.network';
    throw netErr;
  }

  if (!res.ok) {
    // Mirror request()'s i18n-aware HTTP error shaping so callers
    // can hand the error to formatErrorMessage and get the right
    // localised toast.
    let i18nKey = null;
    let i18nParams = null;
    let message;
    try {
      const data = await res.json();
      if (data?.detail && typeof data.detail === 'object' && typeof data.detail.key === 'string') {
        i18nKey = data.detail.key;
        i18nParams = data.detail.params || null;
        message = `[${i18nKey}]`;
      } else {
        message = data?.detail || `Request failed (${res.status})`;
      }
    } catch {
      message = `Request failed (${res.status})`;
    }
    const httpErr = new Error(typeof message === 'string' ? message : JSON.stringify(message));
    httpErr.status = res.status;
    if (i18nKey) {
      httpErr.i18nKey = i18nKey;
      if (i18nParams) httpErr.i18nParams = i18nParams;
    }
    httpErr.isNetwork = res.status === 502 || res.status === 503 || res.status === 504;
    if (httpErr.isNetwork) httpErr.friendlyKey = 'errors.network';
    else if (res.status === 404) httpErr.friendlyKey = 'errors.not_found';
    else if (res.status === 403) httpErr.friendlyKey = 'errors.forbidden';
    else httpErr.friendlyKey = 'errors.unexpected';
    throw httpErr;
  }

  // Extract filename from Content-Disposition; fall back to a
  // generic filename if the header is absent or unparseable.
  const cd = res.headers.get('Content-Disposition') || '';
  const match = cd.match(/filename="?([^";]+)"?/);
  const filename = match ? match[1] : `participant-export-${participantId}.json`;

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  // Defer revocation slightly so Safari/iOS reliably picks up the
  // download. 1s is well past any browser's grab-the-blob window.
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
