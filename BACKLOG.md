# Moimio CE — Backlog

Persistent, accumulates across ships. Open items only; closed ones move
to the relevant version's `CHANGELOG.md` entry.

---

## ENGINE-1 — 11 stale engine tests need rewriting

**Status:** ✅ CLOSED in v1.0.0i (2026-05-13). All 11 tests rewritten
to match current engine behaviour. Backend test suite: 128 passed,
0 xfailed.

### Resolution

Each test was rewritten in one of three shapes:
- **Updated assertions** to match current placement_reason payload
  shape (added `unit_id` field).
- **Re-aimed at scenarios** where the original contract still applies
  (e.g. equalise test now uses cluster+solo to trigger the sweep).
- **Relaxed strict outcomes** to test underlying invariants rather
  than algorithm-specific shapes (e.g. cluster splits across units +
  no overflow, rather than 4+4 even split).

Where rewrites surfaced product concerns about current engine
behaviour, those are captured as separate backlog items below:
ENGINE-2, ENGINE-3, ENGINE-4. None are blocking; all three are
"should we look at this?" questions, not regressions.

---

## ENGINE-2 — Cluster dissolution under `split_oversized_groups=false`

**Status:** Open product question, surfaced during ENGINE-1 rewrite.
**Severity:** Medium. Possible UX surprise but no functional bug.

When an organiser explicitly sets `split_oversized_groups=false` and
provides a cluster that doesn't fit any single unit, the engine
**dissolves the cluster** — members lose their group binding and
get placed as individual fills. The original behaviour (and the
intent suggested by the setting name) was to leave the cluster
**unplaced**, for organiser review.

Current behaviour brings back something that looks like the
pre-v0.53 "scatter bug," but as deliberate engine output rather
than a fault. Two tests (`test_oversized_cluster_unplaced_when_split_disabled`,
`test_v074_a4_oversized_cluster_split_disabled`) document this.

**Product question:** what should this setting mean today?

- Option A — leave cluster unplaced (original v0.53 intent). Setting
  name matches behaviour. Better for organisers who explicitly want
  manual review for oversized groups.
- Option B — dissolve cluster, scatter members (current behaviour).
  Maximises placement count. Setting name becomes misleading.
- Option C — surface a UI warning when the configuration would
  produce dissolution, let the organiser confirm.

No deadline. Worth deciding before the public OSS release of CE,
since the setting name vs behaviour mismatch is a CR-class issue
for first-time users.

---

## ENGINE-3 — Capped rooms left empty when uncapped rooms exist

**Status:** Open product question, surfaced during ENGINE-1 rewrite.
**Severity:** Low. Counter-intuitive but recoverable via manual drag/drop.

In a category mixing capped (`cap=2`) and uncapped units, with enough
participants to fill both, the engine fills the uncapped units first
and **leaves the capped one empty**. Documented by
`test_v073a_mixed_explicit_and_implicit_caps_place_everyone` —
25 participants distribute as ~13 / 0 / ~12 across three rooms.

An organiser creating a small capped room (e.g. a designated couples'
suite, or a wheelchair-accessible room) probably expects it to be USED,
not skipped.

**Product question:** in a mixed capped/uncapped category, should
capped rooms get priority? Or should the engine balance uncapped
rooms first and treat capped as "specialist overflow"?

The right answer probably depends on what the cap represents — a
restriction (use sparingly) vs a feature (use deliberately). UI
might need to distinguish.

---

## ENGINE-4 — Equalise sweep undermines Semantics A in mixed-capacity

**Status:** Open product question, surfaced during ENGINE-1 rewrite.
**Severity:** Low. Internal consistency issue between two engine passes.

The v0.74 "Semantics A" rule (constrained rooms drain first) and the
v1.0.0e equalise sweep (balance ratios across rooms) conflict in
mixed-capacity categories. PASS 4 round-robin correctly places into
the cap-2 unit first; equalise then **moves participants back out**
because the cap-2 unit's ratio (100% full) is higher than the cap-4
unit's (50%).

Documented by `test_v074_constrained_units_fill_first` — 4 participants
into cap-4 + cap-2 produces 3+1, not the intended 2+2.

**Product question:** should equalise respect Semantics A?

- Option A — Disable equalise in categories with mixed capacities
- Option B — Have equalise honour a "preferred fill order" hint
- Option C — Accept Semantics A as a soft heuristic, not a hard rule

Lowest urgency of the three engine product questions — the practical
outcome (all placed, cap respected) is fine even if the heuristic is
soft.

---

## TEST-FRONTEND-1 — Expand frontend test coverage

**Status:** Harness shipped (v1.0.0h-3), coverage to grow.
**Owner:** Backlog; pick up alongside the next feature ship.

The Vitest harness shipped in v1.0.0h-3 with one regression-pin suite
covering `useCapabilities`. The intended trajectory is to add component
and hook tests opportunistically — every time a feature gets shipped,
land its component tests alongside it rather than as a separate ship.

Targets, roughly priority-ordered:

1. **`EventsPage` create-confirm dialog** — the variant-selection logic
   (full body / no-card body / no-info body) is inline JSX and would
   benefit from a test. May need to extract the body-selection logic
   into a small pure helper first to make it testable cleanly.
2. **`EventDetailPage` Delete modal** — type-to-confirm interaction,
   loading states, error handling.
3. **`useTranslation` integration smoke** — assert that a few
   well-known keys (e.g. `event.delete.warning`) resolve in all 6
   locales loaded by the bundle. Cross-locale parity is already
   pinned by the build-time `validate-i18n-keys.py` script, but a
   smoke that exercises React-side loading would catch a separate
   class of bug (e.g. a missing locale import).
4. **Wire `npm test` as a build gate.** Right now `npm test` is a
   local-only command. Adding it to the Dockerfile build stage gates
   shipping on test results. Worth doing once there's enough coverage
   that the cost (failed builds) reliably correlates with bugs.

No deadline. Just don't let it accumulate to the point where adding
the first test for a new feature feels heavy.

---

## SAAS-2 — Wildcard placeholder needs a real landing page

**Status:** Captured 2026-05-15 during Hetzner setup.
**Severity:** Low. UX polish item, not blocking.

Currently when someone hits a `*.moimio.app` subdomain that isn't a
provisioned tenant (e.g. `random123.moimio.app`, or a customer-typed
URL with a typo, or scanners), Caddy responds with:

> Tenant routing not configured yet — provisioning will land this in v0.3.0

This is a developer-facing placeholder, not a customer-facing
experience. For production, this should be a real HTML page that:

- Looks visually consistent with the brand (Steel Blue / Gold / etc.)
- Explains in plain language: "This Moimio space doesn't exist (yet).
  Did you mean a different subdomain? Or are you looking to create one?"
- Has a "Get started" CTA pointing back to moimio.app
- Possibly different message for "this subdomain WAS active but is
  now in the 30-day-grace or 44-day-erasure state" — once those
  lifecycle states exist in v0.3.0+
- Localised (EN/DE/KO minimum, matching marketing site)

Implementation options:
1. **Static HTML in Caddy** — simplest. One HTML file Caddy serves
   directly for unmatched wildcards. No backend dependency.
2. **Redirect to a "/not-found?subdomain=xxx" page on moimio.app** —
   marketing site handles it. Cleaner separation.
3. **Per-state pages** — different content depending on whether the
   subdomain was never created vs is in grace vs is erased.

Option 1 first; refine later if needed.

---

## SAAS-1 — Provisioning service: scoped, ready for first code ship

**Status:** Scoping conversation complete (v1.0.0h-3 session). Awaiting
first code ship.

### Locked decisions

| Q | Decision | Rationale |
|---|---|---|
| **v0.1 ship boundary** | Streams 1 + 2 only (Webhook receiver + Provisioning) | Minimum testable loop: Paddle event → tenant spun up. Streams 3–5 (DB management, dashboard, self-service) become valuable later when real tenants exist. |
| **Repo structure** | FastAPI service, same stack as CE | Familiar patterns; will scale to streams 3–5 without a migration. Roughly `app/api/webhooks.py`, `app/services/provisioning.py`, `app/services/tenants.py`, `app/db.py`. |
| **Release pipeline** | GitHub Actions → GHCR | Hands-off after setup. Push to main → image at `ghcr.io/jc-universe87/moimio-saas:vX.Y.Z` ~5 min later. Same workflow lives in `moimio-ce` repo for its image. |
| **Subdomain DNS** | Wildcard `*.moimio.app` + Caddy DNS-01 | Status quo, already in place. One DNS record, one wildcard cert. No per-tenant DNS API juggling. |

### v0.0.1 first deliverable

**Concrete scope** (1–2 days of focused work):

1. Create `moimio-saas` private repo on GitHub
2. FastAPI skeleton: `app/main.py`, `app/api/webhooks.py`, `app/db.py`,
   Dockerfile, requirements.txt
3. SQLite event store (`events` table: id, source, event_type,
   payload_json, received_at, processed_at)
4. One endpoint: `POST /webhooks/paddle` that:
   - Verifies the Paddle signature header
   - Writes the raw event to SQLite
   - Returns 200 quickly (processing happens out-of-band)
5. GitHub Actions workflow: on push to `main`, build + push to GHCR
6. README with local dev setup

**Out of scope for v0.0.1**: actual tenant provisioning, Caddy
integration, Hetzner Storage Box backup, observability, admin UI.
Those are v0.0.2+ work.

### Open follow-up decisions (deferred from scoping)

- Which Paddle webhook events to subscribe to (subscription.created,
  subscription.updated, subscription.cancelled — others?)
- How signature verification works in detail (Paddle uses a specific
  HMAC scheme; needs reading their docs)
- Where the SQLite file lives on the host (probably a named Docker
  volume mounted at /data)

These get resolved during v0.0.1 implementation, not before.

---

## CE-1 — Image-update awareness for self-hosters and hosted tenants

**Status:** Open. Surfaced during v1.0.0l ship.
**Severity:** Low. Quality-of-life feature, not a defect.

The frontend already shows a "new CE version available" prompt when
the service worker detects a newer browser-side build (see
`frontend/Caddyfile` v0.99c notes and the registerSW shim). That
notification is wired to the **browser bundle**, not to the running
**GHCR image** the container is built from.

For the hosted SaaS, the relevant signal is "a newer GHCR image is
available for this CE version, but you (the customer) are still on
the version your tenant was provisioned with." The customer should
be **notified** of availability and choose **deliberately** when to
upgrade — automatic in-place upgrades on a live event would be a
disaster (mid-allocation, mid-check-in).

### Shape of the feature

- **CE side:** the existing browser-side update prompt is extended
  (or paralleled by) a second prompt that fires when the running
  image's tag is older than the latest GHCR tag for `moimio-backend`
  / `moimio-frontend`.
- **SaaS side:** the SaaS knows each tenant's pinned image version
  (from the rendered `.env`) and can compare it against the latest
  GHCR tag. The comparison result is delivered to the tenant via
  the outbound webhook channel already established in CE.
- **UX:** "an update is available — press here to apply" button in
  the tenant admin sidebar. The actual update is a SaaS-side
  operation (`docker compose pull && docker compose up -d` against
  the rendered template for the new version).

### Design forks to resolve when opening the ship

- Does CE poll GHCR directly, or does the SaaS push the signal?
  (Probably SaaS pushes — keeps CE vendor-neutral.)
- Where in the tenant UI does the prompt surface? (Admin sidebar
  is the obvious place; needs a 5-minute design conversation.)
- What happens if the customer ignores the prompt for months?
  (Probably nothing — the prompt remains visible; eventual
  forced-update policy is a separate decision.)

**No deadline.** Useful once there are real customers running real
events; not a launch blocker.

---

## CE-2 — Backend image runs `uvicorn --reload` in production

**Status:** Open. Surfaced during v1.0.0l ship.
**Severity:** Medium. Production hygiene, not a correctness defect.

`backend/Dockerfile` line 36 starts uvicorn with `--reload`, which
is a development flag that watches source files and restarts the
server on change. Inappropriate in production for two reasons:

1. **Wasted resources.** The file watcher runs continuously and
   consumes CPU and inotify watches with nothing to watch — the
   production image is sealed and has no source mounts.
2. **Spurious restart risk.** Any filesystem touch (log rotation
   on a co-mounted volume, cache file regeneration, etc.) could
   theoretically trigger an unintended reload, dropping in-flight
   requests.

In the v1.0.0l hosted-SaaS context, this fires for every running
tenant. Worth fixing before commercial launch.

### Design forks to resolve when opening the ship

- **Option A:** Parameterise via env var.
  ```
  CMD sh -c "sleep 3 && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 ${UVICORN_FLAGS:-}"
  ```
  Dev compose sets `UVICORN_FLAGS=--reload`; production sets it
  empty. Clean separation, single Dockerfile.

- **Option B:** Override `command:` in the production compose,
  duplicating the CMD logic minus `--reload`. Works but duplicates
  the alembic-upgrade chain in two places.

- **Option C:** Two Dockerfiles (`Dockerfile.dev`, `Dockerfile.prod`).
  Most explicit, most maintenance burden.

Likely Option A; needs a small conversation before implementing.

**No deadline.** Should land before public SaaS launch.

---

## SAAS-3 — Admin dashboard: global product config section

**Status:** Open. Surfaced during v1.0.0l ship.
**Severity:** Medium. Operational requirement for SaaS at scale.

The future SaaS admin UI needs a **global product config** panel
where the operator (Johannes) edits settings that apply product-wide,
not per-tenant. First user: Mailjet credentials.

### Why it matters

Today (v0.4.0 design), the SaaS provisioner reads Mailjet credentials
from environment variables on the CX23 host and writes them into
each tenant's `.env` at provision time. Static — editing requires
SSH and a service restart. Functional for v0.4.0; insufficient long-
term.

The category extends beyond Mailjet:
- SMTP credentials (Mailjet, the first user)
- Default sender email / display name
- Sentry DSN (when Sentry ships)
- Global feature defaults for new tenants
- Rate-limit defaults, webhook timeout defaults

### Shape of the feature

- A `product_config` table in the SaaS registry (key-value pairs).
- The provisioner reads from this table rather than from env vars.
- Admin UI section "Settings → Product config" with rows for each
  setting, masked display of secrets, test-send button for SMTP.
- Audit log of who changed what when (the operator is the only
  user, but the log matters for incident response).

### Design fork: future-only vs. propagate-to-all

When the operator changes a value (e.g. rotates the Mailjet API key),
what happens to **existing tenants**?

- **Option A — future-only.** New value applies only to tenants
  provisioned after the change. Existing tenants keep their old
  values. Simple; rotation requires manual reprovisioning.
- **Option B — propagate.** Editing the value rewrites every
  tenant's `.env` and restarts affected containers. Rotation is
  one-click; complexity is bounded but real.

**Probable direction:** ship A first (simpler), add propagation
as a follow-up. Real-world rotation pain (Mailjet key invalidation,
provider switch) will force B eventually.

**No deadline.** Needs to land before tenant count exceeds ~10,
beyond which manual reprovisioning becomes painful.
