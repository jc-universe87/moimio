# Outbound Webhooks

Moimio CE can send real-time HTTP notifications to external systems
when things happen inside the platform. This page is the integration
guide for self-hosters wiring Moimio into Slack, Zapier, n8n, custom
scripts, or any other service that accepts inbound webhooks.

> v1.0.0g ships the webhook subsystem itself with a single emittable
> event type (`test.ping`) for verification. Real event types — event
> lifecycle, allocation milestones — arrive in subsequent releases.
> The signing scheme, retry policy, and admin UI documented below are
> stable.

---

## What this is for

A webhook is a tiny HTTP POST that Moimio sends to a URL you control,
the moment a system event happens. Common uses:

- **Slack / Teams notifications** — "a new event was just created"
- **Zapier / n8n / Make** — wire Moimio into broader automations
  (sync to a Google Sheet, fire an email, trigger a Notion page)
- **Custom scripts** — your own receiver running on the same network
- **Accounting / CRM integrations** — your finance system finds out
  when a paid event is published

Webhooks are an **optional** capability. If you don't configure any
endpoints, Moimio behaves identically to v1.0.0f. The feature can be
disabled entirely by setting `FEATURE_OUTBOUND_WEBHOOKS=false` in
`.env`.

---

## Configuring an endpoint

Open the admin sidebar → **Webhooks** (Super Admin only). The page
lists your configured endpoints and shows their delivery history.

### Adding a new endpoint

1. Click **Add endpoint**
2. Fill in:
   - **Name** — a label for yourself, e.g. "Slack notifications"
   - **URL** — the receiver URL on the other side. Use HTTPS in
     production; HTTP is accepted but inadvisable. URL fragments
     (`#...`) are stripped automatically since servers never see them
   - **Event types** — comma-separated list of event types this
     endpoint wants, or `*` for everything. For v1.0.0g, only
     `test.ping` is emittable; future releases will add more
3. Click **Create endpoint**
4. **Copy the signing secret immediately.** It is shown once, in a
   modal that refuses to close until you tick "I have saved this
   secret in a safe place". After you close the modal, the plaintext
   secret cannot be recovered through the UI — you would need to
   rotate it to get a new one. (Same pattern as GitHub personal
   access tokens, Stripe restricted keys, etc.)

The secret is what your receiver will use to verify that incoming
webhooks really came from Moimio (not from a random person who
guessed your URL). See [Verifying signatures](#verifying-signatures)
below.

### Per-endpoint actions

Each endpoint card shows the following actions:

| Action | What it does |
|---|---|
| **Send test** | Fires a `test.ping` event right now. Useful for verifying the receiver is reachable and signature-validating |
| **Show deliveries** | Expands the delivery log for this endpoint — the last 50 attempts with response codes, timings, and any errors |
| **Pause** / **Resume** | Temporarily stops the endpoint receiving new events without deleting it |
| **Re-enable** | Resets the state from `degraded` or `disabled` back to `active`. See [Endpoint states](#endpoint-states) |
| **Rotate secret** | Generates a fresh signing secret. The old one is invalidated immediately. You must update your receiver with the new secret before deliveries succeed again |
| **Delete** | Permanently removes the endpoint and its delivery history |

---

## Endpoint states

Moimio tracks the health of each endpoint. The state pill on the
endpoint card tells you what's going on.

| State | Meaning |
|---|---|
| **active** | Healthy. Receiving events normally |
| **degraded** | Five consecutive failed deliveries have occurred. Still receiving new events — Moimio keeps trying — but the UI flags it as a warning. Often a transient issue resolves itself; sometimes it's a sign your receiver is misconfigured |
| **disabled** | Twenty consecutive failures with no success in between. Moimio has stopped firing new events to this endpoint to avoid generating retry traffic that looks like an attack to the receiver. You must investigate and click **Re-enable** to start firing again |
| **paused** | You manually paused it via the **Pause** action. No automatic transitions |

Endpoints recover from `degraded` to `active` automatically on the
first successful delivery. Recovering from `disabled` requires the
admin to click **Re-enable** — this is intentional, to make sure
someone has actually looked at the problem.

---

## Payload format

Every webhook Moimio sends has the same envelope shape:

```json
{
  "event_id": "8a31edf6-6cb3-4901-843b-98a708f4f4eb",
  "event_type": "test.ping",
  "timestamp": "2026-05-12T20:28:20.844612+00:00",
  "data": {
    "message": "This is a test event from Moimio.",
    "endpoint_id": "ef33d910-6f69-41f5-a9ad-b2562b07b61b",
    "endpoint_name": "Smoke Test"
  }
}
```

| Field | Type | Meaning |
|---|---|---|
| `event_id` | UUID string | Unique per event. Use it for receiver-side idempotency — the same `event_id` may arrive multiple times if Moimio retries a delivery your receiver acknowledged but couldn't store |
| `event_type` | string | Dot-separated namespace, e.g. `event.created`, `participant.registered`. v1.0.0g only emits `test.ping` |
| `timestamp` | ISO 8601 string | When Moimio generated the event |
| `data` | object | Event-type-specific payload. Shape depends on the event |

The body is JSON-serialised with sorted keys and no whitespace, so
the same logical payload always produces the same bytes — and
therefore the same signature.

---

## Request headers

Each POST carries:

```
Content-Type: application/json
User-Agent: Moimio-Webhook/1.0
Moimio-Signature: ts=1778618582;h1=8e17009d4a771a4136416ff899e418da5e953aa266399102…
Moimio-Event-Id: 8a31edf6-6cb3-4901-843b-98a708f4f4eb
Moimio-Event-Type: test.ping
```

`Moimio-Event-Id` and `Moimio-Event-Type` are convenience headers
that mirror fields inside the body — useful for routing on the
receiver side without parsing JSON.

`Moimio-Signature` is the integrity check. See below.

---

## Verifying signatures

The signature header has the form `ts=<unix>;h1=<hex>` where:

- `ts` is the Unix timestamp at which Moimio signed the request
- `h1` is `HMAC-SHA256(secret, f"{ts}:{raw_body}")` as a lowercase
  hex digest

On the receiver side, with the secret you copied at endpoint
creation:

### Python

```python
import hashlib
import hmac
import time

WEBHOOK_SECRET = "<the secret you copied>"
TOLERANCE_SECONDS = 5 * 60  # accept signatures up to 5 minutes old

def verify(raw_body: bytes, signature_header: str) -> bool:
    parts = dict(p.split("=", 1) for p in signature_header.split(";"))
    ts = parts.get("ts")
    h1 = parts.get("h1")
    if not ts or not h1:
        return False
    if abs(time.time() - int(ts)) > TOLERANCE_SECONDS:
        return False
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        f"{ts}:".encode() + raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, h1)
```

### Node.js

```javascript
import crypto from 'crypto';

const WEBHOOK_SECRET = '<the secret you copied>';
const TOLERANCE_SECONDS = 5 * 60;

function verify(rawBody, signatureHeader) {
  const parts = Object.fromEntries(
    signatureHeader.split(';').map(p => p.split('='))
  );
  const ts = parts.ts;
  const h1 = parts.h1;
  if (!ts || !h1) return false;
  if (Math.abs(Date.now() / 1000 - parseInt(ts)) > TOLERANCE_SECONDS) {
    return false;
  }
  const expected = crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(`${ts}:`)
    .update(rawBody)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(expected, 'hex'),
    Buffer.from(h1, 'hex')
  );
}
```

### Important: verify the raw body, not parsed JSON

Most web frameworks default to parsing the JSON body before your
handler sees it. The signature was computed over the exact bytes
Moimio sent — if your framework reformats the JSON before you verify,
the signature won't match. Hold onto the raw body bytes; verify
first; parse second.

Express middleware example:

```javascript
app.use(express.raw({ type: 'application/json' }));
app.post('/webhook', (req, res) => {
  const signature = req.get('Moimio-Signature');
  if (!verify(req.body, signature)) {
    return res.status(401).send('invalid signature');
  }
  const event = JSON.parse(req.body.toString());
  // handle event …
  res.status(200).send('ok');
});
```

---

## Retry policy

If your receiver doesn't return a `2xx` response (or doesn't respond
at all within 15 seconds), Moimio retries the delivery on the
following schedule:

| Attempt | Delay after previous attempt |
|---|---|
| 1 | (immediate) |
| 2 | 30 seconds |
| 3 | 2 minutes |
| 4 | 10 minutes |
| 5 | 1 hour |
| 6 | 6 hours |

After the sixth attempt fails, the delivery is marked **exhausted**
and Moimio gives up on it. The same `event_id` is used across all
retries — your receiver should deduplicate by `event_id` to handle
the case where it successfully stored the event but failed to
respond `2xx` in time.

Total retry window: roughly **7.5 hours**. After that, the delivery
is permanently failed (but the row remains in the delivery log for
the retention period, default 30 days).

The retention period is configurable via the
`WEBHOOK_DELIVERY_RETENTION_DAYS` environment variable.

---

## Idempotency

Moimio guarantees **at-least-once** delivery, not exactly-once.

In practice this means:

- If a retry succeeds where an earlier attempt timed out
  mid-response, your receiver will see the same `event_id` twice
- Your receiver should be **idempotent on `event_id`** — typically
  store processed event IDs and reject duplicates

If your receiver returns a `2xx` response, Moimio considers the
delivery successful and will not retry, even if the receiver
internally failed to process the event after responding. Don't
respond `2xx` until you've persisted the event (or accepted that
losing it is fine).

---

## Available event types

The following event types are emittable. The list will grow.

| Event type | Emitted when | Available since |
|---|---|---|
| `test.ping` | Admin clicks "Send test" on an endpoint | v1.0.0g |

(Future event types will be documented here when added.)

---

## Environment configuration

The webhook subsystem is controlled by these environment variables
(set in `.env`):

| Variable | Default | Meaning |
|---|---|---|
| `FEATURE_OUTBOUND_WEBHOOKS` | `true` | Disable the entire subsystem when set to `false` — admin UI hidden, router not registered, scheduler jobs not started |
| `WEBHOOK_DELIVERY_RETENTION_DAYS` | `30` | How many days of delivery history to keep before the daily prune job deletes them |
| `MOIMIO_WEBHOOK_URL` | (empty) | When set together with `MOIMIO_WEBHOOK_SECRET`, Moimio auto-creates a webhook endpoint at first boot subscribing to all events. Intended for deployment automation — most self-hosters leave this empty |
| `MOIMIO_WEBHOOK_SECRET` | (empty) | The signing secret for the auto-registered endpoint above. Required only when `MOIMIO_WEBHOOK_URL` is set |

Auto-registered endpoints have `managed_by="saas"` in the database
and are hidden from the admin UI. They cannot be edited or deleted
through the UI — they are platform infrastructure, not user objects.
Self-hosters who manage their endpoints manually through the admin
UI should leave the two `MOIMIO_WEBHOOK_*` variables empty.

---

## Troubleshooting

### "The receiver returns 200 but I'm not seeing the data"

Check the delivery log — if Moimio shows `status=success` with a
`response_status=200`, the request landed. The problem is on the
receiver side. Verify the receiver actually persisted the event;
many frameworks return `200` before the handler finishes if the
handler throws.

### "I keep getting 'invalid signature' errors"

Three common causes:

1. **You're hashing the parsed JSON, not the raw body.** Most
   frameworks reformat JSON (trailing newline, spaces, key order)
   before your handler sees it. Use the raw bytes
2. **The wrong secret.** Rotate the secret in the admin UI, update
   your receiver, send a test. If that works, the original secret
   on the receiver side was wrong
3. **Clock skew.** Moimio rejects signatures older than 5 minutes.
   If your receiver's clock is far off real time, signatures from
   Moimio will appear stale. Use NTP

### "My endpoint went into the disabled state"

That means twenty consecutive deliveries failed. Likely causes:

- The receiver URL is wrong (typo, fragment, wrong path)
- The receiver is consistently returning a 4xx or 5xx
- The receiver is unreachable from Moimio's container (firewall,
  DNS, certificate issue)

Check the delivery log to see the exact response code and error
message for the last failed attempts, fix the root cause, then
click **Re-enable** to start firing events again.

### "Sending a test event 'does nothing'"

Click **Show deliveries** for the endpoint, then **Refresh**. The
test event is queued as a `PENDING` delivery and fires within
~1 second (the test endpoint triggers an immediate worker tick).
You should see the delivery row with a final status, response code,
and duration. If you don't see a row after 5 seconds, check the
backend logs (`docker compose logs backend`).

---

## Architectural notes

For contributors and developers who want to understand the design
rationale rather than just use the feature, see
[ARCHITECTURE.md § Outbound webhooks](../ARCHITECTURE.md#10-outbound-webhooks-for-integrations).

For the database tables backing the subsystem, see the
[Data Model](data-model.md).
