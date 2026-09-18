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

**Status:** ✅ Resolved in v1.0.0o.

The implementation now matches the documented contract: when an
organiser sets `split_oversized_groups=false` and a cluster does not
fit any single unit (or no unit is eligible at all — e.g. mixed-
gender family vs gendered-only rooms), the whole cluster is left
unplaced for organiser review. A new `held_back` set in the engine
prevents PASS 4a's gender-drain from picking the members up as
individuals after PASS 1 has rejected them as a cluster — the source
of the pre-1.0.0o silent dissolution.

A second reason tag was added: `cluster_no_eligible_unit` (distinct
from `cluster_oversized_split_disabled`) for the "no unit accepts
every cluster member" case, with metadata
`{cluster_genders, available_restrictions}` so the diagnostic UI can
render an actionable message ("Members with group code X could not
be placed. A mixed-gender unit is required.").

Two tests rewritten to assert the correct behaviour
(`test_oversized_cluster_unplaced_when_split_disabled`,
`test_v074_a4_oversized_cluster_split_disabled`); one new test added
covering the Sanchez-class mixed-gender-no-mixed-room scenario.

---

## ENGINE-2-old — Original framing (preserved for context)

The original BACKLOG framing called this an "open product question"
between three options (cluster unplaced, dissolve and scatter, prompt
user). Re-reading the engine docstring at PASS 1 made it clear this
was a defect: the implementation diverged from the documented
contract. v1.0.0o restores the documented behaviour. The product
question is closed.

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

## TEST-BACKEND-1 — Set up dedicated test Postgres so the 96 skipped tests actually run

**Status:** Open.
**Severity:** Medium. Coverage gap, not a regression — visible since
v1.0.0i suite expansion but unblocking the integration tests becomes
more important as the engine accumulates correctness fixes
(v1.0.0o's Sanchez-class fix being the most recent).

### What's happening

Running `pytest` against the production-style backend container on
Nipogi yields **33 passed, 96 skipped** with every skip reporting
the same reason:

```
SKIPPED [1] tests/test_engine_v074.py:137:
  Postgres test DB not reachable: [Errno 2] No such file or directory
```

The 33 passing tests are pure-Python logic tests (engine algorithm
on in-memory fixtures, schema validation, allocation event
serialisation). The 96 skipped tests are db-backed integration tests
that need a real Postgres connection — and `conftest.py` is looking
for a *separate* test instance, not the dev/prod-style db container
serving real data.

The "128 passed" figure from earlier CHANGELOG entries (v1.0.0i and
v1.0.0k) must have been recorded on a machine where a test Postgres
was configured. On Nipogi today, none is.

### What to do

Roughly an hour of work:

1. **Add a `test-db` service** to `docker-compose.yml` (or a separate
   `docker-compose.test.yml`) running `postgres:16-alpine` on an
   internal-only network, exposed only to the backend container.
2. **Point `conftest.py` at it** via a `TEST_DATABASE_URL` env var
   that resolves to the test-db service over Docker DNS. Currently
   `conftest.py` is looking for a unix socket (the `[Errno 2]`
   hint) — switch to a TCP URL pointing at the test container.
3. **Run migrations on session setup.** The conftest fixture
   should `alembic upgrade head` against the test database before
   tests run, then `drop_all` (or `down`) on teardown.
4. **Ensure isolation.** Each test function (or class) should
   start with a clean slate — typically a transactional fixture
   that rolls back at teardown. The existing 96 skipped tests
   presumably assume this is in place; verify their assumptions
   when un-skipping.

### Why now is good timing

Engine correctness work landed in v1.0.0o (the Sanchez-class fix).
Future engine work — and there will be more, given customer use
cases keep surfacing — benefits from the integration tests being
green and gating CI. Wiring this up is the foundation for confident
engine ships.

### Why this isn't urgent

The 33 passing tests *do* cover the v1.0.0o engine logic at the
algorithmic level (pure-Python with in-memory fixtures). The 96
skipped tests are end-to-end variants that confirm the persistence
layer behaves correctly alongside the algorithm. Persistence
patterns haven't changed in many versions, so the coverage gap is
real but contained.

**No deadline.** Worth doing before the public CE release so the
"128+ passed" claim in the CHANGELOG is reproducible from a fresh
clone. Until then, run manual smoke tests for engine changes and
trust the unit-test pass.

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

**Status:** ✅ CLOSED in v1.0.4w (2026-09-18). Surfaced during v1.0.0l ship.

**Resolution.** `backend/Dockerfile` no longer passes `--reload`.

The flag was doing real work in the development compose, which bind-mounts
`./backend/app`, and no work at all in the sealed image, which has no source to
watch. Removing it costs the development stack nothing: `docker-compose.yml`
overrides the command for local work, and a rebuild is what picks up a change to
the image anyway.

Closed alongside the log default (**OPS-1**) in v1.0.4w, both being production
hygiene on the image self-hosters actually run.
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

---

## CE-3 — Next CE zip: inner wrapper folder becomes `moimio/`

**Status:** Note only. Happens when the next CE zip is cut, not before.

The next CE zip renames the inner wrapper folder from `moimio-ce/` to
`moimio/`, removing the scratch-copy step in the CE pipeline. When the rename
happens, the README Quick start gains the unpack step for archive recipients.

---

## PDF-1 — Detailed roster gender column is narrower than its header

**Status:** ✅ CLOSED in v1.0.4w (2026-09-18). Pre-existing; measured during v1.0.4g ship.

**Resolution.** The gender column is now 14mm instead of 10mm
(`pdf_service.py:1164`). The columns summed to 248mm against roughly 267mm
usable on landscape A4, so the 4mm came out of spare and nothing else moved.

Widening was chosen over shortening the headers, as this entry preferred: it
keeps the German abbreviation dot and needs no string change, which matters
because the PDF's translation table is reviewed separately from the locale
files.

`render_detailed` allots 10mm (28.35pt) to the gender column. At
7.5pt bold, two headers overrun it:

| Locale | Header | Fit |
|---|---|---|
| EN | `GENDER` | overruns 2.605pt |
| DE | `GESCHL.` | overruns 3.362pt |
| FR | `GENRE` | 3.110pt clear |
| ES / PT-BR | `GÉN.` / `GÊN.` | 10.872pt clear |
| KO | `성별` | 14.540pt clear |

German has overrun since before v1.0.4g and is unchanged by it.
English inherited the condition when `SEX` became `GENDER`, and
overruns slightly less than German does. The headers touch the
following column rather than overlapping its text, which is why this
has gone unnoticed.

Columns sum to 248mm against ≈267mm usable on landscape A4, so
roughly 19mm is spare. Widening `sex` to 14mm is the obvious fix and
costs nothing elsewhere. Shortening both headers is the alternative
but loses the German abbreviation dot.

Measured on page 1 of six rendered rosters; glyph extents taken from
the content stream, since the merged header words defeat `pdftotext`.

---

## PDF-2 — `units.empty` is unreachable through the export API

**Status:** Open. Surfaced during v1.0.4g ship.

All three renderers print `units.empty` when a group type has no
groups — `render_compact`, `render_detailed`, `render_signin`. None
of those branches can be reached: the pre-flight in `api/export.py`
returns 400 `errors.allocation.no_units` for exactly that case,
before `generate_category_pdf` is called. `export.py` is its only
caller.

Five of the nine string values changed in v1.0.4g are therefore
source-only and cannot be observed in the product. The strings are
correct and should stay; if the pre-flight is ever relaxed they are
already right.

The v1.0.4g `CHANGELOG` entry describes this message as the last
place the old vocabulary survived. That is true of the source, not of
anything a user sees.

Decide one of: relax the pre-flight and let the renderers speak, or
delete the three branches and the six strings.

---

## DASH-1 — Dashboard "unassigned" is derived by subtraction and can go negative

**Status:** Open. Pre-existing; found in session 84 while reading the line for the exclusion work (v1.0.4i). Not fixed there.

`OrganiseDashboard.jsx:470` computes the tile's unassigned figure as
`totalParticipants - allocated_count`. `allocated_count` comes from
`list_categories()` and counts allocation rows, not distinct people. In
an overlapping group type one participant placed in several units is
counted once per unit, so the subtraction under-reports the unassigned
and, once the row count passes the participant count, goes negative.

The distinct figure already exists on the backend: `api/stats.py`
computes `participants_placed` per category from the by-category payload.
Either expose a distinct count from `list_categories()` or have the tile
read the stats payload. File only; no change in v1.0.4i.

---

## DASH-2 — Create and update category return the raw ORM row, so a tile fed from it shows blanks

**Status:** Open, **re-scoped in v1.0.4w** — real at the API, not reachable from any screen. Scheduled for the v1.0.4y counts release. Pre-existing; found in session 84 while reading the endpoints for the exclusion work (v1.0.4i). Not fixed there.

**Re-scope (session 86 survey).** The defect in the endpoints is exactly as
described below and is unchanged. What the entry gets wrong is the consequence:
**no tile is ever fed from those responses.**

`allocationCategories.create` and `.update` have only two callers in the whole
frontend, `GroupTypesEditor.jsx:107` and `:123`, and **both discard the return
value** and immediately `await loadCategories()` instead. So the blanks this
entry describes cannot appear today. `OrganiseDashboard.jsx:474-477` already
carries a comment saying the tile is fed from the list response and never from a
create/update response.

So this is a trap for the next caller, not a live fault: an endpoint that answers
in a different shape from the one that lists the same thing will eventually be
believed by somebody who does not re-list. Still worth the two lines, and it
lives in the same file as DASH-1 and DASH-3, which is why it stays scheduled
rather than closed.

`api_create_category` and `api_update_category` return the
`AllocationCategory` ORM object as the response. That shape omits the
aggregates `list_categories()` adds (`unit_count`, `allocated_count`,
`total_capacity`, and from v1.0.4i `excluded_count`). A tile rendered
from that response shows blanks for those fields until the next list
refetch.

Fix is to have both endpoints answer with the matching entry from
`list_categories()` (one extra query) or with the same dict shape built
for the single row. File only; no change in v1.0.4i.

---

## DASH-3 — `excluded_count` counts exclusion rows for cancelled and removed participants, so the unassigned figure under-reports

**Status:** Open. Pre-existing since v1.0.4i; found in session 85 while reading the dashboard tile for the exclusion UI (v1.0.4k). Not fixed there.

`list_categories()` builds `excluded_count` from a bare count over
`allocation_category_exclusions` (`allocation_service.py:101-109`). It
never joins `Participant`, so the number includes exclusion rows
belonging to people who are no longer in the roster. Nothing removes an
exclusion row when a participant leaves: `participant_service.py` does
not mention `AllocationCategoryExclusion` at all, and
`soft_delete_participant` only stamps `deleted_at`, which leaves the
foreign key's `ON DELETE CASCADE` unused.

Two routes produce a stale row, and both are reachable from the
organiser UI:

- Cancellation — `registration_status` becomes `cancelled`, the row
  survives.
- Soft delete — `deleted_at` is set, the row survives.

The two surfaces that subtract `excluded_count` from a total they have
already filtered by status then take one off too many per stale row:

- `OrganiseDashboard.jsx:479` — `totalParticipants` (line 358) drops
  cancelled participants, and soft-deleted ones never reach the client
  because the roster query filters `deleted_at IS NULL`. The tile's
  unassigned count is low by the number of stale rows, and its
  percentage complete is correspondingly high.
- `EventDetailPage.jsx:853-855` — same subtraction against
  `activeParts` (line 831). This feeds the "closest to done" pick, so a
  group type can be chosen as the quickest win on a figure that is too
  small, or drop out of the running entirely when the subtraction
  reaches zero.

### Scope

Only those two subtractions are wrong. The two places that do the same
job by filtering rather than by arithmetic are correct and need no
change:

- `AllocationBoard.jsx:854-855` filters `activeParticipants` against
  `excludedIds`, so a stale exclusion simply matches nobody.
- `engine_service.py:315` counts what the pre-filter actually removed
  from a pool already restricted to eligible, non-deleted participants,
  so a stale row is never counted.

This narrows the fix: it is a count problem on one aggregate, not a
problem with the exclusion feature.

### Two possible fixes, both open

- Option A — Filter the `excluded_count` aggregate in
  `list_categories()`: join `Participant` and drop cancelled and
  soft-deleted rows. Count-only change, no behaviour change, both
  frontend surfaces untouched.
- Option B — Clear exclusion rows when a participant is cancelled.
  Conceptually cleaner, but it changes behaviour and raises its own
  question: if the participant is later un-cancelled, do they come back
  excluded? Today they do, because the row survives.

Preference, not a decision: Option A. An exclusion records an
organiser's intent about a person, and an unrelated change to that
person's registration status should not destroy it. Whoever picks this
up should still weigh Option B on its merits.

---

## BACKUP-1 — Backup and restore do not know exclusions exist

**Status:** ✅ CLOSED in v1.0.4m (2026-09-17). Export writes
`allocation_exclusions.json`, restore puts the rows back, and a file that
breaks the invariant loses the placement rather than the exclusion. Found in
session 85 phase 1 while tracing every write path to `Allocation` for the
exclusion work (v1.0.4j).

The word "exclusion" does not appear in `backup_service.py`.
`export_event_zip` writes no `allocation_category_exclusions.json`, and
`confirm_restore` restores none. Export an event, restore it, and every
exclusion is silently gone.

The v1.0.4j invariant (no route places an excluded participant) still
holds after a restore: with no exclusions restored there is nothing to
violate, which is why j needs no change to `backup_service.py`. But this
is silent data loss against the stated data-portability promise, and it
must be closed before the feature ships publicly as v1.0.5.

### Resolution

Shipped as v1.0.4m. The member is `allocation_exclusions.json`, written in
both backup modes and always present in a new file, holding `id`,
`allocation_category_id`, `participant_id` and `created_at` per row.

Five decisions settled the shape:

- **An exclusion travels with its person.** Export writes a row only when
  both its participant and its group type are in that export, so a
  cancelled participant's row goes in, a soft-deleted participant's does
  not, and structure mode carries none.
- **The exclusion wins on restore.** A file that says someone is both
  excluded from a group type and placed in it restores the exclusion and
  drops the placement, logs one line naming the new event id and the
  count, and carries on. That keeps the v1.0.4j invariant true through a
  restore, including a restore from a hand-edited file.
- **Optional on read.** `BACKUP_VERSION` stays `"1"` and the member never
  joins `_parse_zip`'s required set. Adding it there would reject every
  backup file made before it existed. An old file restores as "nobody
  excluded"; an older Moimio given a v1.0.4m file ignores the member it
  does not know.
- **No attribution.** Restored rows get `created_by=None`. The user who
  made the decision has no account on the receiving instance, and restore
  carries attribution for nothing else either.
- **Rows are written directly**, never through `add_exclusion`, which also
  writes history rows, vacates units and can re-open a confirmed group
  type. A duplicate pair is dropped before it can reach the UNIQUE
  constraint, so one bad line cannot roll a whole restore back.

The phase 1 note about `preview_restore` carrying user-facing strings is
answered: `RestoreModal.jsx` reads two named counts from the manifest
(`portability.participants_found`, `portability.allocations_found`) and
ignores the rest, so adding a count to the manifest and to the restore
return value needed no new strings and no frontend change.

Five tests in `backend/tests/test_v1_0_4m_backup_exclusions.py` cover the
round trip, an old file, a broken file, a duplicate row and structure
mode. They are the first tests anywhere to export and then restore: before
v1.0.4m, `confirm_restore` and `preview_restore` had no coverage at all.
Everything else that read revealed is filed as BACKUP-2 to BACKUP-6 and
VERSION-1.

---

## K-1 — Excluding out of a keep-as-is unit strands the vacated place

**Status:** Open. Found in session 85 phase 1 while specifying the keep-as-is override for the exclusion work (v1.0.4j). Correct behaviour for j; needs surfacing in v1.0.4k.

From v1.0.4j, exclusion overrides a keep-as-is lock: an excluded
participant comes out of a locked unit like any other. The unit's
`is_kept` flag is left unchanged on purpose, so the place they vacated
stays locked and the engine will not refill it until the organiser
unlocks the unit.

Nothing on screen says this has happened. An organiser who excludes
someone from a locked room sees the room keep its lock and a bed sit
empty across engine runs, with no hint that the two are connected. The
v1.0.4k exclusion UI should show it: at minimum, mark the unit as locked
with a free place after an exclusion-driven removal, or prompt to
unlock it.

---

## STREAM-1 — Exclusion writes broadcast on the organise stream and nothing listens

**Status:** ✅ CLOSED in v1.0.4w (2026-09-18) — **does not reproduce.** Found in session 85 while building the exclusion UI (v1.0.4k). Deliberately not picked up there.

**Resolution.** The premise was already false when this was filed, and the
session 86 survey settled it by reading the consumer rather than the publisher.

Both endpoints do broadcast: `api/allocations.py:433` (`participant_excluded`)
and `:458` (`participant_included`). But the board's stream consumer never
switches on `kind`. `AllocationBoard.jsx:406-418` ignores only the opening
`connected` frame and treats **every other message** as "refetch everything",
debounced by 200ms, calling `loadAll()`. And `loadAll` fetches the exclusion list
along with units and allocations (`AllocationBoard.jsx:486-493`,
`catApi.listExclusions`).

So a second organiser's exclusion does land on this board, inside about a fifth
of a second. This entry says it "only lands when some other event triggers a
refetch"; in fact the exclusion write **is** such an event. The stale claim
survived in a source comment at `AllocationBoard.jsx:59-63`, which is what this
entry was written from.

What remains is only an optimisation — patching `excludedIds` in place instead
of refetching the board — and it is not worth the blast radius into
`useEventStream.jsx` that this entry itself warned about.

**What the next person should watch for instead.** The gap is real, but it is
not exclusions. `patch_participant` (`api/participants.py:276`, the endpoint that
**cancels** somebody, renames them, or changes their group code) and
`delete_participant` (`:421`) publish nothing on any topic. So the board keeps
showing people another organiser has already cancelled. Filed as **STREAM-2**.

The two exclusion endpoints in `api/allocations.py` already publish
`participant_excluded` and `participant_included` on the organise
stream, and have done since v1.0.4i. Nothing subscribes to them
specifically.

v1.0.4k refetches the exclusion list after every write instead (it
rides along with the units and allocations in `loadAll`). That is
correct but coarser: a second organiser's exclusion only lands on this
board when some other event triggers a refetch.

Picking the two events up in `useEventStream` would remove the refetch
and close the staleness window that the `exclusion_cleared` backstop
warning exists to cover. It was left out of v1.0.4k on purpose: it
widens the blast radius into `useEventStream.jsx` for a feature that
had never been on screen.

---

## HIST-1 — `collapseMoves` is category-blind and can invent a cross-group-type "move"

**Status:** Open. Pre-existing; found in session 85 while settling the exclusion phantom-move question for v1.0.4k. Only the exclusion-driven case was guarded there.

`collapseMoves` in `AllocationHistory.jsx` collapses a consecutive
{assign, unassign} pair in the newest-first feed into one "Moved from X
to Y" line. The feed is scoped to one participant but spans every group
type, and the function compares only unit names, never the category. So
removing someone from Room A and later placing them in Team 1, two
unrelated actions in two different group types, renders as "Moved from
Room A to Team 1".

v1.0.4k guarded the one route exclusions made easy to hit (the pair is
not collapsed when the unassign carries `source =
participant_excluded`), because an exclusion vacates units silently and
a later placement elsewhere then sits adjacent to it. The general case
is untouched and predates exclusions entirely.

Fix is to require both rows to carry the same `category_id` before
collapsing. `category_id` is already on the serialised row. Not done in
v1.0.4k because it changes how existing, unrelated history reads and
deserves its own before/after check.

---

## PANEL-1 — Popped-out participant panel resizes width but not height, and docks back too short

**Status:** ✅ CLOSED in v1.0.4w (2026-09-18). Found in manual testing of v1.0.4k (2026-09-17).

**Resolution.** One cause, and it was not where this entry looked.

The resize handler is innocent: `startPanelResize`
(`AllocationBoard.jsx:108`) and the pointer-move handler (`:117`) both write `w`
and `h`, and the style applies both (`:2148`). The height **was** being set.

The clamp came from somewhere else. `AllocationBoard.jsx:447-458` matched the
docked panel's height to the units grid beside it by writing an inline
`maxHeight`. It checked `isMobileView` and **nothing else** — not
`panelFloating` — so it kept clamping the panel while it floated, from the
*units grid's* height. An inline `max-height` beats an inline `height` whenever
it is smaller, and width has no such clamp. Hence: width moved, height did not.
"Docks back too short" was the same line, because the value was written with
`.style` imperatively and React never cleared it.

v1.0.4w scopes that effect to the docked, desktop case and clears the value on
cleanup.

**Two things the session 86 survey settled that this entry could not.**
**Nothing is stored anywhere** — `panelSize` is plain component state with a
fixed default (`AllocationBoard.jsx:105`), and there is no `localStorage`, no
`sessionStorage`, no user preference and no event setting holding a panel size.
So there was nothing saved earlier for the fix to repair. And Johannes's
impression that this differed between older and newer events is really **few
units against many**: the clamp was the units grid's height, so an event with
twenty units had a loose clamp and one with two had a tight one.

The Excluded block's own half of this — a long list escaping the card — shares
this cause but also needs the block to scroll inside itself. That half is
**EXCL-3**, in the v1.0.4x pass.

The resize grip on the floating participant panel (`AllocationBoard.jsx`,
`startPanelResize`) writes both `panelSize.w` and `panelSize.h`, but only
the width visibly changes. Dragging the grip downward does not make the
panel taller.

Docking it again then leaves the container too short for its contents and
the participant list overflows the panel instead of scrolling inside it.

Both halves point at the same place: the floating panel sets an explicit
`height: panelSize.h` and the pool inside it is `flex: 1 1 0`, while the
docked panel has no height at all and the pool is bounded by `minHeight
24rem / maxHeight 70vh`. Whatever the resize writes has to survive the
switch between those two sizing regimes, and at the moment the docked
regime ignores it. Worth resolving together with the pool cap added in
v1.0.4l, which is the third thing now writing to that height.

---

## NAV-1 — Sidebar active state is inconsistent: Einteilung, Backup and Webhooks never highlight

**Status:** ✅ CLOSED in v1.0.4w (2026-09-18). Found in manual testing of v1.0.4k (2026-09-17).

**Resolution.** The audit this entry asked for turned up **two separate causes**
and **a fourth affected entry nobody had reported**.

**The rule the working entries follow.** `activeSection` comes from the
`?section=` query parameter (`AdminLayout.jsx:123-124`, `:204-205`), and an entry
highlights when `activeSection === item.id` (`:389`, `:424`, `:467`).
`navigateSection(id)` puts that id in the URL (`:158-167`). So an entry
highlights only if clicking it puts its own id there.

**Cause 1 — Einteilung.** `AdminLayout.jsx:124` aliases the old v45 value
`organise` to `board`. Three nav items still carry `id: 'organise'` (`:219`,
`:246`, `:255`). Clicking one navigates to `?section=organise`, the alias
rewrites the value to `board`, and the test then asks whether
`'board' === 'organise'`, which is false forever. The item at `:234` carries
`id: 'board'` and highlights correctly, which is why this looked arbitrary from
outside.

**Cause 2 — Backup, Webhooks and Workspace.** These navigate to paths, not
sections, and their `className` strings were **hardcoded to the inactive style
with no conditional at all**: `AdminLayout.jsx:512`, `:530`, `:544`. There was no
logic to be wrong.

**Workspace is the fourth one,** and it was never reported because it is visible
only on managed instances (`capabilities.account_portal`).

**Users was the odd one out** and showed the intended shape: a bespoke
`location.pathname === '/admin/users'` test at `:499`, the only one anybody had
written.

v1.0.4w fixes both causes: the section comparison is normalised the same way the
value is, and the four path entries share one `pathActive` helper. `/admin`
(NavLink's own `isActive`) and Manage account (an external link, correctly never
highlighted) were already right and are untouched.

Selecting **Benutzer** in the sidebar highlights it as the active entry.
Selecting **Einteilung**, **Backup** or **Webhooks** does not — the entry
opens, but nothing in the sidebar shows where you are.

Almost certainly one rule for deciding "is this entry active" that matches
the path for some entries and not others (nested route, query-string tab,
or a path prefix that does not match). One fix should cover all three, and
the audit should check every sidebar entry rather than only the three
reported.

---

## EXCL-1 — Cannot drag a participant out of the Excluded block

**Status:** Open, accepted for now. Found in manual testing of v1.0.4k (2026-09-17).

Dragging a participant **onto** the Excluded block excludes them. Dragging
one **out** of it does nothing; the only way back is the undo control on
the chip, or selecting the chip and using the selection bar.

The chips inside `ExcludedBlock.jsx` are not draggable, and the block's
own handlers call `stopPropagation` so a drag started there would not
reach the board's drop targets anyway. Deliberate for v1.0.4k: the click
route works and is reversible. Filed so the asymmetry is recorded, not
because it blocks anything.

---

## EXCL-2 — Excluded names truncate at high counts because the undo label is long

**Status:** Open. Found in manual testing of v1.0.4k (2026-09-17).

Each chip in the Excluded block is `name + undo control` on one line, with
the name truncating. The undo label is a word, not an icon
(`organise.exclude.undo`), and in the longer locales it takes enough of a
256px panel that the name is cut short. The more people are excluded, the
more chips are affected at once, so it reads as a "high counts" problem
even though every chip has it.

Options, none picked: shorten the label, use an icon with the existing
title text, put the control on a second line, or widen the panel while the
block is open.

---

## BACKUP-2 — The backup drops columns, and restore reads two it never gets

**Status:** ✅ CLOSED in v1.0.4q (2026-09-17). Every column is now carried,
reset on purpose, or left out for a stated reason, and the register holds no
`known_gap:BACKUP-2`. Found in session 86 phase 1 while reading the backup path
for BACKUP-1 (v1.0.4m).

`export_event_zip` writes a literal field list per model, passed to the
`_row` helper. Nothing is picked up automatically, so a column added to a
model after its list was written is silently dropped from every backup.
Dropped today:

- Event: `timezone`, `details_confirmed`, `registration_confirmed`,
  `is_archived`, `over_cap_signalled`
- AllocationCategory: `name_key`, `item_label_key`,
  `exclusive_group_codes`, `confirmed`
- AllocationUnit: `mark_restriction`, `is_kept`
- MarkDefinition: `cluster_behaviour`, `created_by_user_id`
- MarkAssignment: `assigned_by_user_id`
- CustomFieldDefinition: `show_in_form`
- ParticipantPreferenceRequest: `resolved_note`
- Participant: `override_group_room`, `checked_in_at`
  (`confirmation_token` is rightly excluded: it is a secret)
- the `updated_at` family: not exported on eight tables, and exported but
  ignored on Event

`show_in_form` is the one with an outward-facing consequence. It is NOT
NULL and defaults True, and False is the value that marks a field as
admin-only (auto-created from a CSV import, meant for the People page and
not for registrants). So a restore puts every such field back on the
PUBLIC registration form.

Two columns are exported and then overridden. `confirm_restore` forces
`has_capacity` and `has_gender_restriction` to `True` with the comment
"v1.0.3: ignored; always on". Phase 1 found no code path that can set
either to False any more, so this may be correct rather than a gap; it is
tagged as a gap in the v1.0.4n register until somebody proves the columns
can only ever be True, at which point they become `derived` and the
columns are candidates for removal.

`confirm_restore` reads `name_key` and `item_label_key` when it builds a
restored category, but export never writes either, so both are always
absent and a restored event loses its translated default type names and
falls back to the stored English text. The read and the write have never
been exercised against each other, which is how the asymmetry survived.

Several of the dropped columns are allocation rules the organiser set, the
same class of data as BACKUP-1: a unit's mark restriction and its
keep-as-is lock both vanish on a round trip. Some of the others may be
deliberate (`confirmed` and `is_archived` arguably should not survive into
a restored draft), but none is documented as such, so this needs deciding
column by column rather than in one sweep.

`duplicate_event_config` in `event_service.py` already does the harder
parts correctly and is the model to copy: it rewires `mark_restriction`
through a `mark_id_map`, carries both name keys, and forces
`confirmed=False`.

Restore also writes placeholder ids into `event.created_by` and
`notes.author_id`: the new event's own id sits in a column that means
"which user did this". Nothing validates or resolves it, so it has been
harmless, but it is not a real value.

v1.0.4m adds the first round-trip test over this code. Extend it as each
column is fixed.

### Resolution

Shipped as v1.0.4q, applying the decisions below column by column.

**Carried**, and each one proved on a restored event through its real reader
where it has one: `timezone`, `is_archived`, `override_group_room`,
`checked_in_at`, `show_in_form`, `name_key`, `item_label_key`,
`exclusive_group_codes`, `is_kept`, `cluster_behaviour`, `resolved_note`, and
`mark_restriction`, which is `remapped` through `mark_map` rather than copied
because it is a real foreign key. v1.0.4p's write order is what made that
possible: marks are now written before units.

**Left out, each with its reason in the register** rather than as a gap:
`over_cap_signalled` is `instance_state`; `details_confirmed`,
`registration_confirmed`, `confirmed`, `has_capacity` and
`has_gender_restriction` are `reset_on_restore`; `created_by_user_id` and
`assigned_by_user_id` are `not_meaningful_elsewhere`.

**Attribution.** `events.created_by` and `notes.author_id` are the restoring
user, declared `placeholder` with `not_meaningful_elsewhere`. With no actor
the pre-existing stand-in stays, because both columns are NOT NULL and there
is no blank to leave.

**Three columns whose values the app looks up or validates** get the model
default when the file's value is not one the app would accept, and the fall
back is counted: `name_key` and `item_label_key` against the app's own
`NAME_KEYS` and `ITEM_LABEL_KEYS`, and `cluster_behaviour` against
`("together", "split", "none")`. **`timezone` is the exception**: the app has
no notion of a valid zone anywhere, so it is carried as it is. There is no
`VALID_TIMEZONES` beside `VALID_DATE_FORMATS` and `VALID_LANGUAGES` in
`api/user_preferences.py`, nothing checks the zone on the event or preference
write paths, and nothing in the backend imports `zoneinfo` or `pytz`: the
value is written at creation and read once, into the per-person GDPR export.
Validating it on restore would have made a restore stricter than
registration, which is a product decision and not this release's to take.

**The `name_key` asymmetry that started this entry is gone.** Restore read
`name_key` and `item_label_key` for a field export never wrote; now export
writes both and the round-trip net checks them.

Covered by `test_v1_0_4q_columns_and_dates.py`, and the net's fixture now
holds a non-default value for every newly carried column.

### Decided (session 86)

Column by column, so v1.0.4q has nothing left to weigh up.

**Carried.** `timezone`, `is_archived`, `name_key`, `item_label_key`,
`exclusive_group_codes`, `mark_restriction`, `is_kept`, `cluster_behaviour`,
`checked_in_at`, `show_in_form`, `resolved_note`, `override_group_room`. An
archived event comes back archived: losing the flag would un-archive
something the organiser deliberately put away, which is a silent change in
the more permissive direction.

**Not carried, with the reason each gets in the register.**

- `over_cap_signalled` is `instance_state`. It is the sending instance's
  plan-enforcement state, not the event's. Carried across it would either
  suppress a signal a hosted tenant is entitled to, or re-fire one already
  sent.
- `mark_definitions.created_by_user_id` and
  `mark_assignments.assigned_by_user_id` are `not_meaningful_elsewhere`.
  NULL is already the modelled meaning of a "system mark", and the screen
  renders it. Carrying the old id would show every mark as made by an
  unknown user, or worse, match a real user on the receiving instance.
- `details_confirmed`, `registration_confirmed` and
  `allocation_categories.confirmed` are `reset_on_restore`. Every ordinary
  edit already clears them, and a restore is the largest edit there is; the
  organiser re-ticks them before opening registration.
- `has_capacity` and `has_gender_restriction` stay forced to `True`, also
  `reset_on_restore`. The code deliberately keeps these retired flags true
  for rollback safety, so writing anything else back would fight it.

**Attribution.** `events.created_by` and `notes.author_id` are the
restoring user: the only truthful answer on the receiving instance, and the
only non-null one, since both columns are NOT NULL. Notes have worked this
way since v1.0.4o; `events.created_by` follows in v1.0.4q.

Whether `override_group_room` should exist at all is a separate question,
filed as ARCH-2. It is carried either way: dropping a column from a backup
because it currently looks unused is how the next silent loss happens.

---
v1.0.4m adds the first round-trip test over this code. Extend it as each
column is fixed.

---

## BACKUP-3 — Ids inside JSON fields are not renumbered on restore

**Status:** ✅ CLOSED in v1.0.4p (2026-09-17). All three columns are now
`remapped`: every id the restore's maps know is translated in place, and
everything else is left exactly as the file has it. Found in session 86 phase 1
while reading the backup path for BACKUP-1 (v1.0.4m).

Restore renumbers every id that lives in its own column, through the five
maps in `confirm_restore`. Ids that live inside a JSON field are copied
across verbatim, so they still point at pre-restore ids that exist nowhere
on the receiving instance. The rule each one expresses silently stops
working, with nothing on screen to say so:

- `participants.group_code_categories` — a list of group type ids, or NULL
  for all of them
- `participant_preference_requests.category_scope` — a list of group type
  ids, unless it is the literal `"all"`, which is safe
- `allocation_categories.settings.engine.mark_priorities` — entries of
  `{id, behaviour}` keyed on a bare mark id, read by
  `_mark_behaviour_for` in `allocation_service.py`

An exclusion is not affected: it stores both of its ids as real columns,
which is why v1.0.4m could map them cleanly.

### Resolution

Shipped as v1.0.4p, in two parts.

**The write order moved** so that every map exists before anything needs it:
event, marks, custom field definitions, field configs, group types, units,
participants, exclusions resolved, allocations, exclusion rows, mark
assignments, preferences, notes. Marks moved from tenth to second and
participants from fourth to seventh. Nothing inside any block changed beyond
what the move required. This also clears the way for v1.0.4q to carry
`mark_restriction`, which needs `mark_map` before units are written.

**One rule for all three columns:** translate every id the maps know, and
leave every other value exactly as the file has it, in place. Order and
length never change, and nothing is added or dropped. "Every other value"
covers `null`, `"all"`, ids the maps do not know, and elements of an
unexpected type. In `mark_priorities`, only an entry's `id` is ever
translated: every other key in the entry survives, both on-disk entry
shapes are handled, and the bare id is never given a `mark:` prefix.

**Why nothing is dropped**, which is the decision this release turned on.
The investigation first proposed dropping ids that do not resolve. That is
wrong, and the reason is in `engine_service`:

```
scope = p.group_code_categories
if scope and cat_id_str not in [str(s) for s in scope]:
    continue
```

It is a falsy check, and its own comment reads "default = all categories".
So an EMPTY list means "applies to every group type", while a list of ids
that resolve to nothing means "applies nowhere". Dropping the last
untranslatable id would therefore have inverted the rule rather than losing
it, and could have put people together in group types the organiser had
deliberately taken their group code out of. Leaving the untranslatable in
place keeps every reader's behaviour identical to what it was before the
backup, whatever the list holds.

In a file the app produced every id resolves, because export carries every
group type and every mark. An id that does not resolve was already dead
before the backup was taken, which is ARCH-3, not a backup gap.

Covered by `test_v1_0_4p_write_order.py`, twelve cases, each checked through
the column's real reader where one enforces it: the engine's PASS 1
clustering for `group_code_categories` and `_mark_behaviour_for` for
`mark_priorities`. `category_scope` is checked as a stored value only,
because nothing enforces it: that is ARCH-4. The round-trip net now covers
all three columns, and carries one unresolvable id to prove it comes back
untouched.

---

## BACKUP-4 — Event data the backup does not carry at all

**Status:** ✅ CLOSED in v1.0.4s (2026-09-17). Check-in and notes are carried,
and staff roles are recorded as deliberately not carried. Found in session 86
phase 1 while reading the backup path for BACKUP-1 (v1.0.4m).

**Resolution.** All three parts, in the order the entry raises them.

- **Check-in.** `checkin_fields` and `checkin_values` join the register, in a
  new optional `checkin.json` member shaped like `marks.json`. The columns go
  in both modes, because they are part of the event's shape. The ticks go in
  full backups only, and only for participants the export carries, so a
  removed person's ticks stay behind exactly as their exclusions do. Restore
  writes the columns straight after the field configs and the ticks straight
  after the participants, and drops a duplicated (participant, column) line
  before it can reach the table's UNIQUE constraint.
- **Notes.** A note is now carried when what it is about is in the export:
  the event, an exported participant, a group type or a unit. Restore
  translates `notable_id` by its type instead of overwriting it with the
  event, and copies `is_published` instead of forcing it True. A note whose
  type is not one of those four, or whose target the file does not carry, is
  skipped and counted, and the restore carries on.
  - **Private notes.** A private note is visible in the app only to its
    author, and any event admin can download a backup, so `export_event_zip`
    gained a `private_notes` keyword whose default carries none. The per-event
    download passes the downloader's id; the leaving export
    (`app.cli.export_all`) passes `ALL_PRIVATE_NOTES`, because that file is
    the organisation's own copy of its own data and is produced from a shell
    that already has full database access. A restored private note stays
    private, authored by whoever restored it.
  - The `author_id` foreign key hazard this entry predicted was already fixed
    in v1.0.4o, before any file could contain a note.
- **Staff event roles.** `event_user_assignments` stays uncarried, and its
  reason changes from `known_gap:BACKUP-4` to `not_meaningful_elsewhere`: a
  permission must never come from a file. Who may see or change an event is
  decided where it is restored, by inviting the team again. The restore
  screen line that says so is in STRINGS-1.

The original entry follows, as the record of what was found.

Whole tables, not just columns, are outside the backup:

- check-in fields and values (`checkin_fields`, `checkin_values`): the
  event's check-in questions and every participant's answers
- every note except published event-level ones: participant, unit and
  category notes, and all unpublished notes, are dropped
- staff event roles (`event_user_assignments`): possibly deliberate, since
  users exist per instance and would not resolve on the receiving one

The hosted export runs CE's `app.cli.export_all`, which calls
`export_event_zip` per event, so the hosted GDPR data export inherits all
of this unchanged. Fixing it in CE fixes it for hosted tenants with no
control-plane change.

The notes gap is worse than "all but published event-level notes". **No
screen creates an event-level note.** The three places that open the notes
modal pass `participant` (`EventDetailPage.jsx`, `CheckinOverlayPage.jsx`),
`category` and `unit` (`AllocationBoard.jsx`), and the export filter is
`notable_id == event_id AND is_published`. So `notes.json` is always `[]`
in any event built through the app, and the restore block that reads it has
never run.

Two consequences follow from that block never running:

- Restore writes the new event's own id into `notes.author_id`, which is a
  real foreign key to `users.id`. A file that did contain a note would
  therefore fail the constraint and roll the whole restore back. The bug is
  invisible only because the member is always empty.
- The Backup page hint for a full backup claims "Everything:
  participants, allocations, responses, notes"
  (`backup.mode.full.hint`). The notes part is untrue today, and so is
  "everything".

### Decided (session 86)

**Team roles are never carried.** A permission must never arrive from a
file. Restore is Super Admin only, which limits who can trigger it but not
who can craft the file, so carrying `event_user_assignments` would let a
hand-edited ZIP grant a third party `event_admin` on the restored event.
The restore screen tells the organiser to re-invite the team (STRINGS-1),
which is also the right moment to review who still needs access.

**Notes: every existing kind is carried**, in full backups only, and only
for things that are themselves in the backup. So a note on a participant
who is not in the export goes with them.

- An event backup carries every **shared** note, plus only the
  **downloading user's own** private notes. A private note is visible to
  its author alone, and a backup must not become a way around that.
- The **workspace export for a leaving customer** carries **everyone's**
  notes. The customer is the controller and it is all their data; the
  leaving screen says so (STRINGS-1).
- A restored private note **stays private**, authored by the restoring
  user.

**Structure-only backups carry no notes at all.** The text is unvalidated
and the file is offered for sharing between organisations.

**Check-in follows the standing rules:** fields in both modes, because they
are configuration and exactly what a template is for; ticks in full backups
only, and only for people in the backup.

---
  (`backup.mode.full.hint`). The notes part is untrue today, and so is
  "everything".

---

## BACKUP-5 — Allocation history is not in the backup

**Status:** ✅ CLOSED in v1.0.4t (2026-09-18). The history is carried, and
with it **the backup register holds no gaps at all**. Found in session 86
phase 1 while reading the backup path for BACKUP-1 (v1.0.4m).

**Resolution.** `allocation_events` joins the register in a new optional
`allocation_events.json`, written last on restore because one row can name a
participant, a unit, a group type and, inside `meta`, a mark. The three
decisions this entry said were needed, as settled:

- **The actor is not carried.** `actor_user_id` is always NULL on restore.
  That account does not exist on the receiving instance, the column is
  nullable by design, and the history screen already renders a missing actor
  as a removed user, so no new string was needed.
- **A row travels with its person.** Only rows whose participant is in the
  export go in, which drops rows about removed people and rows whose
  `participant_id` an erasure has already nulled. A row whose participant
  does not resolve on restore is skipped and counted.
- **The ids inside `meta` are translated** by the v1.0.4p rule: every id the
  maps know, and everything else left exactly as the file has it. The trap is
  `cluster_id`, which holds `mark:<mark id>` for a mark cluster and the group
  code itself for a group-code cluster; a group code is free organiser text
  that may legitimately begin with `mark:`, so it is never touched.

Two further decisions the entry did not anticipate:

- **Names of people the backup does not carry are dropped** from
  `placement.cluster_members`, while `cluster_size` and
  `cluster_placed_here` are left alone. The counts describe what happened, so
  a line may say three and name two, which is truthful; changing the numbers
  would not be.
- **A unit or group type that does not resolve becomes NULL** and is counted,
  which is what the database itself does when the row is deleted
  (ON DELETE SET NULL). The name snapshots keep the line readable.

**The register now holds no `known_gap` tag**, on a column or in
`NOT_CARRIED`, and `test_v1_0_4t_history.py` test 13 fails if one is ever
added: the check `BACKUP_REGISTER_DOC` has promised since v1.0.4n, which says
v1.0.5 ships only when no gap remains. `event_user_assignments` stays
uncarried under `not_meaningful_elsewhere`, which is a decision and not a
gap: a permission must never come from a file.

The original entry follows, as the record of what was found.

`allocation_events` is not exported at all. After a restore an event has
its exclusions and its placements in force and an empty history: no record
of who placed or excluded whom, or when. From v1.0.4m that is stated in
the CHANGELOG rather than left to be discovered, but it is still a gap.

Exporting it needs three decisions first, none of them obvious:

- actor ids (`actor_user_id`), since those users do not exist on the
  receiving instance, and the existing placeholder pattern writes a value
  that is not a user id
- the `unit_name_snapshot` and `category_name_snapshot` columns, which are
  organiser text and may name a person
- ids inside the `meta` JSONB, including the `mark:<uuid>` cluster ids the
  engine writes (see BACKUP-3)

### Decided (session 86)

**History is carried.** The names of people who are not in the backup are
removed from the placement details inside it, so some lines will name fewer
people than they did: a line that read "placed with Anna, Bruno and Carla"
may come back naming only two of them. That is a real loss of fidelity and
it is the right trade, because the alternative is either carrying the names
of people the backup is not allowed to mention, or dropping the reasoning
line for everyone.

---
- ids inside the `meta` JSONB, including the `mark:<uuid>` cluster ids the
  engine writes (see BACKUP-3)

---

## BACKUP-6 — participants.csv shows no exclusions

**Status:** ✅ CLOSED in v1.0.4v (2026-09-18). Feature request, not a defect. Found in session 86 phase 1 while reading the backup path for BACKUP-1 (v1.0.4m).

**Resolution.** Both exports carry exclusions now.

`participants.csv` has an **"Excluded From"** column, straight after
`Marks` and before the custom fields, so no existing column moved. The cell
holds the group type names the person is excluded from, stored names as
they are, separated by `", "`, exactly as `Marks` does, and empty when
there are none. It is built by one query joining
`allocation_category_exclusions` to `allocation_categories` on the event,
grouped in Python beside the marks lookup it copies. The header is a
literal English list, so this needed no key and touched no locale file.

A cancelled participant keeps their exclusions in the file. An exclusion
records what an organiser decided about a person, and an unrelated status
change does not undo it. Removed people were already out, because
`list_participants` filters `deleted_at`.

`data_export_service.export_participant_data` gained an **`exclusions`**
key of `[{category_name, created_at}, ...]`, sitting beside `allocations`,
its nearest relative, and resolved the same way: the group type's stored
name, never a raw id. `created_by` is deliberately not in it, for the same
reason `allocation_history` drops `actor_user_id` — which admin decided is
the controller's metadata, not the data subject's data. The export is
served as a raw JSON download with no presentation layer, so no label was
needed and no translated string either. `EXPORT_SCHEMA_VERSION` was left at
"1.0": an added key breaks no consumer.

`test_v1_0_4v_exclusions_in_exports.py` holds the whole of it, asserting
the entire header in order so a column that moves fails there.

**This closes the backup and export work.** BACKUP-1 to BACKUP-11 are all
resolved, the register in `backup_service.py` holds no gaps, and v1.0.4v is
the last release of the series. What remains beside it is filed elsewhere:
the strings in STRINGS-1, the roster PDF page, the converging serialiser in
ARCH-1, and the hosted leaving email in SAAS-4.

The original entry follows, as the record of what was found.

`GET /api/events/{event_id}/export/participants.csv` in `api/export.py`
has no exclusion column, and runs no query for one. A spreadsheet of
participants gives no sign that anyone is excluded from anything, so an
organiser working from the CSV cannot see a decision they made in the app.

The natural shape is one column listing the group types each participant
is excluded from, matching how the existing `Marks` column flattens mark
names into one comma-separated cell.

The per-person GDPR export omits them too.
`data_export_service.export_participant_data` returns ten keys covering
custom fields, marks, preferences, allocations, allocation history, notes
and check-in values, resolving every foreign key to a readable name, and an
exclusion is the one recorded decision about that individual that is
missing. An `exclusions` key of `[{category_name, created_at}, ...]` would
match how `allocations` becomes `{unit_name, category_name, created_at}`.

### Decided (session 86)

Both go ahead. `participants.csv` gains an **"Excluded From"** column,
holding group type names as stored, comma separated, in the shape the
existing `Marks` column already uses. The header is a literal English list,
so it needs no new string. The per-person GDPR export gains its
`exclusions` key too.

---

## VERSION-1 — `check-version-markers.py` does not read the `version.py` docstring

**Status:** ✅ CLOSED in v1.0.4w (2026-09-18). Found in session 86 phase 1 while reading the version markers for v1.0.4m. Corrected by hand there, not fixed.

**Resolution.** Both halves, as this entry said were needed.

`scripts/bump-version.py` now rewrites the line-1 docstring alongside
`__version__` and `moimioVersion`, asserting exactly one substitution the way the
other two already did. `scripts/check-version-markers.py` now reads the docstring
as a fourth marker and fails when it disagrees with the rest.

CI picks it up with no workflow change, because `.github/workflows/build.yml:47`
already runs the checker on every push and on every `v*` tag.

This is the last release whose brief has to say "then set the docstring by
hand".

`backend/app/version.py` names the version twice: in `__version__`, and in
its own line-1 docstring. `scripts/bump-version.py` sets only the first,
and `scripts/check-version-markers.py` never reads the second, so the
docstring can drift without CI noticing.

It already has. At v1.0.4l the docstring read `(v1.0.4k)`, one release
stale. v1.0.4m sets it by hand, which fixes the value but not the cause.

Two ways to close it, neither picked: have `bump-version.py` rewrite the
docstring alongside `__version__`, or have `check-version-markers.py` read
it as a fourth marker so a mismatch fails the CI `checks` job. The second
is the stronger guard, but it only works if the first exists too.

---

## BACKUP-7 — The units loop records a unit before checking it

**Status:** ✅ CLOSED in v1.0.4o (2026-09-17). The map entry is now written
below the guard, so a unit whose group type is missing is skipped and never
reaches `unit_map`. Found in session 86 phase 1 while reading the restore
path for BACKUP-1 (v1.0.4m).

In `confirm_restore`, the units loop fills `unit_map` before the guard that
skips a unit whose group type is missing from the file:

```
unit_map[unit_src["id"]] = new_unit_id
new_cat_id = category_map.get(unit_src["category_id"])
if not new_cat_id:
    continue
```

So a unit whose group type is absent lands in the map although no row is
ever created for it. An allocation naming that unit then passes the
`if not new_p_id or not new_unit_id` test, and the insert violates the
foreign key to `allocation_units.id`, which rolls back the entire restore.
One bad line costs the whole file.

Reachable only from a hand-edited or truncated file, which is expected
input: a backup is a plain unsigned ZIP.

The fix is to move the map write below the `continue`. That changes the
failure mode rather than removing it: an allocation naming a skipped unit
would then be skipped silently, which is the intended behaviour, but it
means a file with a missing group type quietly loses those placements. Say
so in the release notes.

Every other block was checked for the same pattern and is safe: the custom
field, participant, category and mark loops all write their map entry with
no guard following, and the v1.0.4m `unit_category_map` is deliberately
written after the guard.

### Resolution

Shipped as v1.0.4o. The `unit_map` write moved below the guard, and the
guard grew: a unit is skipped when its group type does not resolve, when it
has no usable name, or when it has no capacity. The consequence is recorded
as intended behaviour rather than left to be discovered: a file with a
missing group type silently loses the placements in it, and the counts the
restore returns say how many lines went.

Every map-filling block now also declines to use an empty or missing old id
as a key, so a row with no id of its own is still created but nothing in the
file can refer to it.

---

## BACKUP-8 — Restore re-dates every row

**Status:** ✅ CLOSED in v1.0.4q (2026-09-17). A full backup keeps every
original timestamp; a structure backup is dated when it is restored. Found in
session 86 phase 1 while reading the restore path for BACKUP-1 (v1.0.4m).

Every restore block omits the timestamp columns from its insert, so the
server default supplies the value and every row is dated to the moment of
the restore. `created_at` is exported for eleven tables and restored for
none of them; `updated_at` is not exported at all except on Event, where it
is exported and ignored. v1.0.4m followed the same pattern for exclusions,
for consistency rather than because it is right.

This is not cosmetic. The columns are read on screen:

- `participants.created_at` is the "Registered at" column on the People
  table and the check-in desk, a sort key, the insight panel's registration
  date, the "recent sign-ups" list, and the registration sparkline.
- `events.created_at` orders the events list, and is the sparkline's
  origin.
- `notes.created_at` is shown on every note.
- `participants.checked_in_at` is the check-in time column (and is not
  exported at all: see BACKUP-2).
- `allocation_events.occurred_at` is the entire history timeline (see
  BACKUP-5).

So a restored event shows every participant registering in the same second
on the day of the restore, a sparkline collapsed to one spike, and a
meaningless "recent sign-ups".

All of these can be set on insert. Each is a `server_default`, which
applies only when the INSERT omits the column, and there are no database
triggers anywhere in the schema. `occurred_at` uses `clock_timestamp()`
specifically so rows written in one transaction get distinct ordered
values, so if history is ever restored, passing the original values is
required and not merely preferable.

`_parse_date` truncates to ten characters and returns a `date`, so it needs
a datetime sibling before this can be done.

### Resolution

Shipped as v1.0.4q.

**Export** gained `updated_at` on the six members that lacked it, appended
after each member's existing columns so no existing position moved.

**Restore** writes every exported `created_at`, `updated_at` and
`checked_in_at` as the file has them, through a new `_parse_datetime` beside
`_parse_date`, which is left alone because it serves the date columns and
deliberately truncates. Only a timezone-aware value is accepted: every
timestamp column is `DateTime(timezone=True)` and export writes
`isoformat()`, so an app-made file always carries the offset, and a naive
value would be a guess about which zone it meant.

**A structure backup restores no timestamps.** It is a new event built from
someone's setup, so the model defaults apply. The mode is read once from
`manifest.json`, and only the exact value `"structure"` counts: a missing or
unknown mode means a full backup, because files older than the distinction
carry no mode at all.

**A value the file lacks is not damage**, and the model default applies. A
value it has that will not parse is damage, and is counted in a new
`defaulted` ledger reported beside v1.0.4o's `skipped` and `shortened`.

**Nothing overwrites a restored `updated_at`.** `onupdate=func.now()` fires
on UPDATE only, and `confirm_restore` issues nothing but INSERTs: it holds no
`db.refresh`, no `db.execute`, no `db.merge` and not one assignment to an ORM
attribute after construction. There are no ORM event listeners and no
`@validates` anywhere in `backend/app`, and no database triggers. The one
place the trap could have been sprung was the round-trip net's own fixture,
which used to set a unit's mark after the unit was flushed; the marks block
moved ahead of the units so every value is set at construction.

### Decided (session 86)

**The original dates are kept.** A backup that says an event was created on
the day it was restored is not a faithful copy, and these columns are read
on screen: "Registered at", the sort order, the recent sign-ups list and the
registration sparkline all come from `participants.created_at`.

---
`_parse_date` truncates to ten characters and returns a `date`, so it needs
a datetime sibling before this can be done.

---

## BACKUP-9 — A damaged or hand-edited file can still fail the whole restore

**Status:** ✅ CLOSED in v1.0.4o (2026-09-17). Every line-level problem now
costs its own line and whatever depended on it; a member that cannot be read
refuses the file before anything is written. Found in session 86 phase 1
while reading the restore path for BACKUP-1 (v1.0.4m).

A backup is a plain unsigned ZIP, so a hand-edited file is expected input,
and the rule is that what does not map is skipped and one bad line never
rolls back the whole restore. Today it can, six ways:

- **Bracket reads raise `KeyError`.** Eighteen of them, across the custom
  field, field config, participant, category, unit, allocation and mark
  blocks. `row["id"]` on the participant CSV is the sharpest: a CSV missing
  the `id` column raises rather than skipping.
- **Duplicate allocation lines** break `UNIQUE (participant_id, unit_id)`.
  Exactly the case v1.0.4m fixed for exclusions and left standing in the
  adjacent block. `mark_assignments` has no unique constraint, so duplicates
  there insert silently instead.
- **Explicit nulls reach NOT NULL columns.** `unit_src.get("capacity")` has
  no default and `capacity` has been NOT NULL since v0.74; the four name and
  label fields have the same exposure once a key is present but null.
- **A member of the wrong JSON type.** A member that parses but is a dict
  where a list is expected iterates its keys as strings, and the first
  bracket read then raises `TypeError`.
- **Strings too long for their columns** raise `DataError` at flush: group
  type and unit names are `String(100)`, labels and participant names
  `String(255)`. Nothing truncates.

Two related defects belong here:

- `_safe_enum` falls back to `CONFIRMED` for an unrecognised
  `registration_status`, where the model's own default is `PENDING`. A bad
  value silently promotes someone into the active roster.
- `_OPTIONAL_MEMBERS` copies its defaults with `list(default)`. Correct for
  the list default it has today; for a dict default it would silently yield
  a list of the keys. Use `copy.deepcopy` and widen the annotation when the
  second optional member is added.

`_parse_date`, `_parse_int` and `_parse_json_field` already degrade instead
of raising, and are the pattern the rest of the restore should follow.

### Resolution

Shipped as v1.0.4o, on two rules.

**A damaged line costs its own line.** Every one of the eighteen bracket
reads became a forgiving read through one helper, which falls back to the
column's OWN default, read from the model so it cannot drift, and skips the
line when the column is NOT NULL with no default. Restore never invents a
value the model does not define. Duplicates are dropped with the first
winning, by old id in every block that fills a map and by pair for
allocations, exclusions and mark assignments. Over-long text is shortened to
the column's declared length. A line of the wrong type inside a well-shaped
member is skipped.

**A member that cannot be read refuses the file.** Invalid JSON, a member
whose top-level shape is wrong, and a `participants.csv` with no `id`
column are all refused in `_parse_zip`, before any row is written, at
preview and at confirm alike. They surface as the existing 422 rather than
as a 500; `errors.export.zip_missing_files` is the closest key and names the
member, and STRINGS-1 carries the specific wording it deserves.

Both related defects are fixed too. `_safe_enum` now falls back to the
model's own `PENDING` rather than `CONFIRMED`, so a bad status no longer
quietly promotes somebody into the active roster. `_OPTIONAL_MEMBERS`
defaults are deep-copied and the annotation is widened.

One case the entry did not list turned up while writing the tests: an
explicit null in a NOT NULL column that HAS a default still reached the
insert as None, because `.get(key, literal)` returns the literal only when
the key is absent. Those reads now go through the same helper.

v1.0.4p added the one de-duplication v1.0.4o left conditional. Custom field
values have no unique constraint on (participant, field), so the question
was whether the app can legitimately write two. It cannot: registration
iterates a dict keyed by field id, and the update path builds
`existing_by_field_id` and upserts. So a repeated line is damage, and the
first one now wins, counted like every other skip.

The whole of it is covered by `test_v1_0_4o_damaged_files.py`, and
`test_v1_0_4o_round_trip.py` proves that a file Moimio produced restores
exactly as it did before.

---

## BACKUP-10 — There is no whole-workspace restore

**Status:** ✅ CLOSED in v1.0.4u (2026-09-18). Found in session 86 phase 1 while tracing the hosted leaving path for BACKUP-1 (v1.0.4m). Not a data-loss bug.

**Resolution.** `python -m app.cli.import_all --in <path> --as <email>`
restores a whole-workspace export in one command, run inside the backend
container the way `export_all` is. `--as` names an existing Super Admin on
the receiving instance; an unknown address or a user of any other role is
refused and nothing is written. Every event in the archive is restored
through `backup_service.confirm_restore`, the same per-event restore the
Backup page uses, with that admin as the actor, so every rule v1.0.4m to
v1.0.4t settled applies unchanged.

- **`--dry-run`** writes nothing at all: it opens the archive, reads each
  event file through `preview_restore`, and lists what would come back.
  (v1.0.4v: it always runs, whatever the instance already holds, and shows
  the name each event would end up with. Looking first must never need a
  flag whose name says "write".)
- **`--into-existing`** is the only way to *really* restore onto an
  instance that already has events, archived ones included.
- **Names.** On an instance with no events each event keeps its own name.
  With `--into-existing`, names get " (Restored)". This is
  `confirm_restore`'s new `suffix_name` keyword, whose default is the
  Backup page's behaviour, so every existing caller and test is untouched.
- **One bad event costs that event.** Its failure is caught, its own work
  rolled back, and the run carries on with the next event. The summary
  names every event as restored or failed, with the reason, and the exit
  code is 0 only when every event was restored, following `export_all`'s
  convention.
- **A single-event backup is refused** with a message sending it to the
  Backup page, before a database session is even opened.

**The two reference lists.** `team.json` and `webhooks.json` join the
whole-workspace export and are always present, empty or not. `team.json`
carries each account's name, email, system role, `is_active`,
`can_manage_users`, `can_create_events`, and its per-event roles and
permissions keyed by the event ids the manifest already lists.
`webhooks.json` carries `managed_by == "user"` endpoints only, with name,
address, event types and active flag. Never carried: `hashed_password`,
`password_reset_token`, `password_reset_expires`, a webhook `secret`, and
any SaaS-managed endpoint. Both files carry a `note` saying they are for
reference and that restoring never applies them. Neither is ever part of a
per-event backup, because an event admin can download one of those.

**Nothing is applied.** The command never creates a user, never grants a
role and never registers a webhook; it does not read either list at all. A
permission must never come from a file. The register is unchanged, with a
comment beside `NOT_CARRIED`'s `event_user_assignments` entry noting that
the workspace export carries the team as a list to read.

`test_v1_0_4u_workspace_restore.py` holds the whole of it, including a test
that searches every decompressed byte of the archive for a password hash, a
reset token and a webhook secret.

**The documentation page** landed at `docs/moving-a-workspace.md`, linked
from `docs/manual/09-data-export-gdpr.md` and
`docs/installation/quick-guide.md`. The remaining follow-up, the hosted
leaving email, is filed as SAAS-4.

The original entry follows, as the record of what was found.

`app.cli.export_all` writes an outer archive holding `manifest.json` plus
`events/<event_id>.zip` per event, and the hosted control plane runs exactly
that command inside the tenant container to produce the leaving export.
**Nothing reads it back.** There is no endpoint, command or script in CE or
on the control plane that opens the outer archive or its manifest.

So a customer with twenty events unzips the bundle themselves and uploads
twenty files one at a time through the restore modal, as Super Admin, each
arriving as a separate draft renamed "(Restored)", in whatever order they
happen to click.

The workspace shape lives only in the outer manifest, which nothing reads:
which events existed, their order, and their archived flag. Every event's
own data is in the file, so nothing is lost. What is missing is the
difference between "you can leave" and "you can leave in an afternoon".

### Decided (session 86)

**A server command** restores every event in a whole-workspace export,
archived ones included, through the same checked per-event restore. So every
v1.0.4o rule about damaged lines applies unchanged.

- **A trial run** shows what would be restored without writing anything.
- **Damaged events.** If one event cannot be read, the rest still restore,
  and the command lists what did not. The same rule one level up: one bad
  event costs that event, not the archive.
- **Names.** On an empty server, events keep their real names. If the server
  already has events, the command stops unless it is told explicitly to add
  to them, and in that case names get "(Restored)".
- **Every event comes back as a draft**, attributed to the admin named in
  the command.
- **Two reference lists join the whole-workspace export.** Restore never
  applies either of them, and both files are always present, empty or not.
  - **The team:** names, emails, system roles and per-event roles. No
    passwords and no tokens.
  - **Webhooks:** customer-made endpoints only, never the hosting service's
    own. Names, addresses and event types; no secrets. For hosted customers
    this list is always empty, because the Webhooks page is not visible to
    them.
- **Not in per-event backups.** Both lists appear only in the
  whole-workspace export.
- **The leaving screen** says what the export contains (STRINGS-1).

Follow-ups outside this code: a self-hosting documentation page, and the
hosted leaving email should explain how to use the file, which is a wording
change in `moimio-saas`. Both are settled by v1.0.4u: the page is
`docs/moving-a-workspace.md`, and the email is SAAS-4.

---

## USER-1 — Deleting a user does not handle their notes

**Status:** Open. Found in session 86 phase 1 while reading `notes.author_id` for the backup work (v1.0.4m). Not fixed there.

`api/users.py` deletes a user with a bare `db.delete(user)` and no sweep of
anything they authored. `notes.author_id` is a foreign key to `users.id`
declared with no `ondelete`, so the database default applies and deleting
anyone who has ever written a note likely fails with an integrity error
surfaced as a 500.

Unverified: whether the deployed schema actually carries that constraint.
The baseline migration builds the schema from the frozen v50b snapshot, and
the model declares the foreign key, so the test database (built from
`Base.metadata`) definitely has it. Confirming the deployed one needs a
`\d notes` against a real database.

Options, none picked: reassign a deleted user's notes to whoever deleted
them; delete their unpublished notes and reassign the published ones; add
`ondelete="SET NULL"` and make the column nullable, which is a migration
and changes the visibility rule, since an unpublished note is visible only
to its author.

---

## ARCH-1 — Group type and unit settings are copied by three separate paths

**Status:** Open, after v1.0.5. Found in session 86 phase 1 while reading the backup path for BACKUP-1 (v1.0.4m).

Three code paths copy allocation categories and units, each complete to a
different degree, and the least complete one is the backup:

- `backup_service.export_event_zip` / `confirm_restore`: drops `name_key`,
  `item_label_key`, `exclusive_group_codes`, `mark_restriction` and
  `is_kept`, and copies `settings` with stale mark ids inside it.
- `event_service.duplicate_event_config`: introspects
  `Model.__table__.columns` rather than using a hand list, rewires
  `mark_restriction` through a `mark_id_map`, carries both name keys, and
  forces `confirmed=False`.
- `room_layout_io`: carries everything the other two do plus
  `exclusive_group_codes` and `is_kept`, and rewrites both
  `mark_restriction` and `settings.engine.mark_priorities` from ids to mark
  NAMES so a layout is portable across instances.

The same bug class has already been found and fixed once in one of them.
`room_layout_io` carries the comment "v1.0.3 fix: this was omitted, so
importing a layout silently reverted 'group codes claim units exclusively'
to off" — the identical omission the backup still has.

Converge the three on one serialiser. The v1.0.4n register and guard are
the cheap version of this: they make an omission fail a test rather than
ship. This entry is the real fix, and it is not urgent enough to hold
v1.0.5.

---

## STRINGS-1 — Strings to deliver in one batch before v1.0.5

**Status:** Open. New series, opened in session 86 during the backup work (v1.0.4o).

Six locale files, and the i18n validator only checks one direction: it never
checks that the other five match English. Johannes reviews DE and KO himself
and his corrections are applied character for character. So a string change
is not cheap, and dribbling one key per release through that review five or
six times is the wrong shape.

This entry collects every string the backup work needs, to be delivered
once, in one release, before v1.0.5.

### Wrong today

- **`backup.mode.full.hint`** reads "Everything: participants, allocations,
  responses, notes. For backup and restore." Both "everything" and "notes"
  are untrue: the backup carries no notes an organiser can create, no
  check-in answers and no history. Rewrite it once the backup releases have
  landed and the sentence can be made true. This is the one string that is
  a false product claim rather than a missing one.

### Needed by work already done

- **The restore success panel should say how many lines could not be
  restored.** v1.0.4o returns per-member skipped and shortened counts in the
  restore result, and the modal ignores keys it does not know, so the counts
  are already there and invisible. One or two keys, in the shape of the
  existing `portability.participants_found`.

  **This must also cover v1.0.4q's `defaulted` counts**, which are the third
  ledger the restore returns: a value the file carried that restore could not
  use, so the column's own default applies instead. "Skipped" and
  "defaulted" are different things to an organiser, and only the second one
  leaves a row in place with a changed value, so the wording has to
  distinguish them. v1.0.4s adds nothing new to the ledgers: a note it
  cannot place and a duplicated check-in tick both count as skipped, under
  `notes.json` and `checkin.json:values`.
- **A backup file that cannot be read needs its own message.** v1.0.4o
  refuses an unreadable member with `errors.export.zip_missing_files`, "The
  backup ZIP is missing files: {files}", passing the member name. It is the
  closest existing key: it is about the backup rather than a generic
  failure, it names the member, and it already surfaces as a 422 at both
  preview and confirm. But it says "missing" where the truth is "present and
  unreadable", so an organiser could go looking for a file that is there. A
  new key should say that a part of the backup could not be read, and name
  it. Cases to cover: invalid JSON, a section of the wrong shape, and a
  participant list with no id column.

### Pending a decision

- **The restore screen says that team members and their roles are not part
  of a backup**, if `event_user_assignments` stays uncarried. A new key
  beside `portability.restore_as_new_hint`.
- **The leaving (Danger Zone) screen says what the leaving export
  contains**, so a customer knows before they click what they will get back
  and what they will have to set up again.

### Added by v1.0.4q

- **The restore success button should open the restored event.** It reads
  `portability.go_to_events` ("Go to events") today, and that stopped being
  the helpful destination in v1.0.4q: restored events keep their original
  dates, so they sit in the list where the originals sat instead of at the
  top, and an organiser restoring a two-year-old event has to hunt for it.
  The restore result already returns `new_event_id`, so the button can go
  straight there.

  **No existing key fits.** The nearest is `events.menu.open_label`
  ("Actions"), which is the accessibility label on a row's overflow menu, not
  an action. So this needs one new key and a frontend change to navigate by
  id, not a wording change alone.

### Added by v1.0.4s

- **A rejected form field needs a translated message.** FORM-1 found the
  public registration form showing FastAPI's raw 422 body, in English, with
  internal field paths, under a translated heading. At least one key is
  needed for the commonest case, in the shape of "Please enter a valid email
  address", and the survey in FORM-1 decides whether the rest come from the
  server as `{"key": ...}` or from one shared formatter in the frontend. The
  key count is not settled until that decision is.

- **Whatever DATE-1 settles about times and time zones** may need wording: a
  label for a time-zone list if the free-text box becomes one, and any "shown
  in the event's time zone" note a screen needs. Nothing is needed until that
  survey decides, so this is a placeholder with no key count.

### Removed by v1.0.4r

- **`prefs.scope`** is now unused in all six locale files, and should be deleted
  in the same batch. v1.0.4r removed the only thing that read it: the label
  above the group-type scope in the grouping-requests panel, which showed raw
  ids for a setting nothing ever acted on. The key sits at line 894 of each of
  the six files. It is the only key this release left unused.

### Decided (session 86)

Both lines above are now decided, and both are needed.

- The restore screen **does** say that team members and their roles are not
  part of a backup, because BACKUP-4 settles that they are never carried.
- The leaving screen **does** say what the export contains, and it must
  also say that the export carries **everyone's notes**, including private
  ones, since BACKUP-4 settles that too. A customer should know that before
  they click, not after.

  **Added by v1.0.4u:** the same line must also say that the export carries
  **two reference lists**, the team and the customer's own webhooks, and
  that neither is applied by restoring. No passwords, no reset tokens and
  no webhook secrets are in either. The customer should know before they
  click that they will have to invite their team again and re-enter their
  webhook secrets on the receiving server.

---

## BACKUP-11 — A structure-only backup still carries personal data

**Status:** ✅ CLOSED in v1.0.4s (2026-09-17). A structure backup now leaves
both fields out, and carries no notes either. Found in session 86 phase 1
while reading structure mode for the backup work (v1.0.4o).

**Resolution.** In structure mode the export drops `email_from_name` and
`email_reply_to` from the event's settings before writing `event.json`. A
full backup keeps both: that is the same organisation restoring its own
event. The event row in the session is never touched, only the copy written
to the file.

The same release settled the larger question this entry sits beside: a
structure backup carries **no notes at all**, whatever the caller asks for.
Notes are what people wrote about each other and about the event, never part
of its shape, and a structure backup is made to be shared outside the
organisation.

The original entry follows, as the record of what was found.

Structure mode is offered as "Structure only (GDPR-safe)" with the hint
"Event shape without any personal data. Share as a template between
organisations.", and `export_event_zip`'s own docstring says it "deliberately
contains NO personal data. Safe to share with another organisation as an
event template, version-control, email between staff, etc."

It keeps `event.json` whole, and two of its fields are personal data:

- `events.settings.email_from_name` — a real person's name, used as the
  sender name on registration email.
- `events.settings.email_reply_to` — a real email address.

Both are read at `api/events.py` when a registration email is composed. They
are not incidental free text like the event's own name: they are contact
details for a named individual, and they travel under a promise that the
file contains none.

The event's `name`, `description` and `location` are free organiser text and
could in principle name someone too, but stripping them would make a
template useless, so they are a different case and are left alone.

**Decision pending:** leave both fields out of `event.json` in structure
mode, keeping them in full mode. That is a two-line filter on one member and
needs no schema change. The alternative, doing nothing, means the GDPR-safe
claim is not quite true.

### Decided (session 86)

**Structure-only backups leave out `email_from_name` and `email_reply_to`.**
Both stay in a full backup. They are contact details for a named individual
and the file travels under a promise that it holds none.

---

## ARCH-2 — `participants.override_group_room` is a column nothing reads

**Status:** Open. Found in session 86 phase 1 while listing the columns the backup drops (BACKUP-2). Not a defect.

`override_group_room` is Boolean, NOT NULL, default false. Searching the
whole backend and frontend finds it in four places and no more: the model,
two schema fields, and `data_export_service`, which puts it in a
participant's own GDPR export. **Nothing reads it for behaviour** — not the
engine, not `allocation_service`, not any screen.

The name suggests "let this person override their group's room", which
would be a real allocation rule, so either the feature was never finished
or it was removed and the column outlived it.

It is carried in a backup from v1.0.4q onward, decided under BACKUP-2: a
column that currently looks unused is exactly the kind of thing that gets
dropped and then turns out to matter, and it already appears in a
participant's GDPR export as their data.

Options, none picked: wire it up, if the rule was intended; drop the column
in a migration, if it was not; or leave it and document it as reserved.
Whichever it is, the answer should be written down rather than rediscovered.

---

## ARCH-3 — Deleting a group type leaves its id behind in two JSON columns

**Status:** ✅ CLOSED in v1.0.4r (2026-09-17). Both columns are retired, so a
leftover id is now unread and has no effect. Found in session 86 while settling
the v1.0.4p rule for ids inside JSON.

**Resolution.** Rather than teach `delete_category` to tidy these columns,
v1.0.4r retired what they were for. The engine no longer reads
`participants.group_code_categories`, and nothing ever read
`participant_preference_requests.category_scope`, so a dead group type id in
either one changes nothing: a group code now applies in every group type where
`use_group_codes` is on. The stored values stay for one release for rollback
safety, and step 2 (ARCH-5) drops both columns, which removes the stale data
along with them.

The warning below still holds for anyone working on the restore path before
step 2, because restore keeps translating these lists until the columns go.

The original entry follows, as the record of what was found.

`delete_category` deletes the row and flushes, and nothing else. It does not
touch either column that holds group type ids inside JSON:

- `participants.group_code_categories`
- `participant_preference_requests.category_scope`

So a deleted group type's id stays in live data indefinitely. The
consequences, in order of how much they matter:

- **If every group type a group code was limited to is deleted, the code
  silently applies nowhere.** The engine's PASS 1 reads the scope with
  `if scope and cat_id_str not in [...]`, so a list of dead ids matches no
  category and the participant is never clustered. Nothing on screen says
  why the group code stopped working.
- **Recreating the group type does not bring the limit back.** The new row
  has a new id, so the stale one still matches nothing.
- **What the screens show for such a person is unknown** and worth checking
  while fixing this.

**Warning for whoever picks this up: never fix it by emptying the list.** An
empty list means "every group type" to the engine, so emptying a stale
scope would widen a group code from "nowhere" to "everywhere". That is the
trap v1.0.4p found and deliberately avoided; see BACKUP-3's Resolution.

The safe shapes are to remove only the deleted id and leave any others, or
to clear the group code alongside the scope when the scope would be left
with nothing live in it. Either needs a decision about what the organiser
should see.

---

## ARCH-4 — Grouping-request scopes are stored and exported but do nothing

**Status:** ✅ CLOSED in v1.0.4r (2026-09-17). The scope is retired. Found in
session 86 while settling the v1.0.4p rule for ids inside JSON.

**Resolution.** The choice that had no effect is gone rather than made to work.
Registration no longer reads `category_scope`, so every row takes the column's
default from here on, and `PreferencesPanel.jsx` no longer renders it, which
also ends the raw-UUID display described below. A backup and the GDPR export
still carry the column until step 2 (ARCH-5) drops it, so that a backup, the
export and the database agree on what is stored.

The original entry follows, as the record of what was found.

`participant_preference_requests.category_scope` holds `"all"` or a list of
group type ids, is written at registration, is carried in a backup, and
appears in the per-person GDPR export. **Nothing enforces it.** The string
`category_scope` appears nowhere in `engine_service.py` or
`allocation_service.py`, so a request scoped to one group type is honoured
exactly as widely as one scoped to all of them: the organiser reads the
request and acts by hand.

There is a second, smaller problem beside it. `PreferencesPanel.jsx` renders
the scope as `req.category_scope.join(', ')`, which puts **raw UUIDs** on
screen when the scope is a list rather than `"all"`. Nothing resolves them
to group type names.

So either the column should drive something, or the UI should stop offering
a choice that has no effect, and in the meantime it should at least show
names rather than ids. v1.0.4p carries the ids correctly through a restore,
which is all that release could sensibly do about it.

---

## ARCH-5 — Step 2: drop the retired limit columns, once v1.0.5 has run safely

**Status:** Open, and deliberately not before v1.0.5. Opened in session 86 as
step 2 of v1.0.4r, which retired both limits (see ARCH-3 and ARCH-4).

v1.0.4r stopped reading and writing two columns but left them in place, so that
a rollback to v1.0.4q or earlier still finds the data it expects. Once v1.0.5
has run safely in the field, they go.

**The columns:**

- `participants.group_code_categories`
- `participant_preference_requests.category_scope`

**What step 2 removes:**

- **Both columns, by migration.** One Alembic revision, dropping both.
- **Both model fields and their RETIRED comments**, in
  `backend/app/models/participant.py` and
  `backend/app/models/preference_request.py`.
- **The backup register entries**, in `backend/app/services/backup_service.py`:
  `"group_code_categories": Col(True, "remapped")` under `participants`, and
  `"category_scope": Col(True, "remapped", raw=True)` under
  `participant_preference_requests`. Note the declaration-order rule when
  editing the register: non-raw exported columns come before `raw` ones.
- **The export and restore handling for both**, in the same file: the
  `json.dumps` of `group_code_categories` in the participants CSV writer, the
  `| {"category_scope": pr.category_scope}` in the preference-requests writer,
  and both `_translate_id_list(...)` calls in `confirm_restore`.
- **`_translate_id_list` itself.** These two calls are its only callers, so it
  is orphaned the moment they go. `mark_priorities` is translated by a
  different path and is unaffected.
- **The net fixture's parts and the p test cases for these columns:** the
  fixture values, the net's own self-checks and the reference entries in
  `backend/tests/test_v1_0_4o_round_trip.py`, the translation cases in
  `backend/tests/test_v1_0_4p_write_order.py`, the register expectations in
  `backend/tests/test_v1_0_4n_backup_guard.py`, and
  `backend/tests/test_v1_0_4r_limits_retired.py`, whose whole subject is these
  two columns.
- **The GDPR export keys**, in `backend/app/services/data_export_service.py`:
  `category_scope` (twice, in the two preference-request shapes) and
  `group_code_categories` (once, in the participant shape).
- **The `make_participant` keyword** `group_code_categories` in
  `backend/tests/conftest.py`, if nothing still passes it.

**One detail for any count or clean-up query written before the drop.**
`participants.group_code_categories` is `JSONB` without `none_as_null=True`, so
a row with no limit holds the **JSON `null` literal**, not SQL NULL.
`WHERE group_code_categories IS NULL` therefore finds nothing.
`WHERE group_code_categories = 'null'::jsonb` is the test that works. Python
reads both back as `None`, which is why this is invisible from the application
side.

---

## FORM-1 — A rejected form field shows the server's raw validation error

**Status:** Open. Found by Johannes's manual test in session 86. Belongs to the
non-backup survey before v1.0.5.

The public registration form was given the email `rest@gmail.com3242`, which
the server rightly rejects. The form then showed:

- the heading "Einige Felder müssen überprüft werden", correctly translated
- underneath it, FastAPI's raw 422 body as JSON, in English, including
  internal field paths such as `"loc":["body","email"]`

So a registrant who mistypes their email is shown the inside of the server. It
is in the wrong language, it names fields by their internal path, and it does
not say which box to go back and fix.

**Expected.** The email field itself is marked, with a translated message such
as "Please enter a valid email address", and no raw JSON appears anywhere.

**What the survey must do:**

- **Find every form that can receive a 422, and how each one renders it.**
  Registration is the one that was tested; the admin forms have their own
  error handling and may differ.
- **Decide where the fix belongs.** Either one shared formatter in the
  frontend that turns a 422 body into per-field messages, or a server-side
  validation-error handler that returns the app's own `{"key": ...}` shape so
  every client gets a translatable message. The second is the shape the rest
  of the app already uses for errors.
- **Decide whether obvious mistakes should be caught before sending,** so a
  mistyped email is marked as the registrant types rather than after a round
  trip. That is a separate decision from how a 422 is rendered, and both are
  needed.

The wording this needs is filed in STRINGS-1.

---

## DATE-1 — Dates on screen ignore the user's date-format setting

**Status:** Open. Found by Johannes's manual test in session 86, on the v1.0.4s
build. Belongs to the non-backup survey before v1.0.5.

The settings panel had **Sprache: Deutsch** and **Datumsformat: YYYY-MM-DD
(ISO)**, with the **Zeitzone** box empty. The People list's "REGISTRIERT AM"
column then showed `7/10/26, 2:09 PM` on every row: American month/day/year
with a 12-hour clock. That is neither the chosen format nor German, so the
preference is not reaching this column at all.

**Expected:** every date and every time on screen follows the chosen format.

There is already a shared formatter, and this column simply does not use it.
`frontend/src/hooks/useDateFormat.jsx` holds `formatDate`, which reads the
preference and handles all six values of `VALID_DATE_FORMATS`.
`PeopleTable.jsx` imports it and uses it for the date of birth, but the
"Registered at" cell calls
`new Date(p.created_at).toLocaleString(undefined, {...})` instead, and
`undefined` means "the browser's own locale".

So this is not only a missed call. `formatDate` takes a date and returns a
date: it has no notion of a time, and "Registered at" needs both. Whatever
the survey decides has to cover times as well, which is why this is a survey
item and not a one-line fix.

**What the survey must do:**

- **Find every place the frontend renders a date or a time, and which of them
  read the preference.** The People list is the one that was tested. Eleven
  files use the hook today, and eight still call `toLocaleDateString`,
  `toLocaleString` or `toLocaleTimeString` directly: `AllocationHistory.jsx`,
  `CheckInPanel.jsx`, `MarkAssignModal.jsx`, `NotesModal.jsx`,
  `PeopleTable.jsx`, `RestoreModal.jsx`, `RegisterPage.jsx` and
  `WebhooksPage.jsx`. Some of those may be correct; none of them was checked.
- **Decide on one shared formatter that every screen uses,** covering times as
  well as dates, so this cannot drift again. The hook's own comment already
  defers long-form dates for want of `Intl.DateTimeFormat`, which is the same
  decision.
- **Look at the time zone box in the same panel.** It is free text, it was
  empty, and the backend validates no zone anywhere (see BACKUP-2's
  Resolution: `events.timezone` is carried through a backup as it is, because
  there is nothing to validate it against). Decide whether a time is shown in
  the user's zone or the event's, and whether the box should offer a list
  instead of free text.
- **Add any new strings to STRINGS-1.**

---

## SAAS-4 — The hosted leaving email does not say how to use the export

**Status:** Open. Opened in session 86 alongside v1.0.4u, which closed
BACKUP-10. **Not a change to this repo.** It is a wording change in
`~/dev/moimio-saas`, filed here so it is not lost.

v1.0.4u gives a leaving customer a whole-workspace export and one command
that restores all of it onto their own Moimio, plus a documentation page
(`docs/moving-a-workspace.md`) that walks through it. The hosted leaving
email still hands over the file and says nothing about either.

What the email should say, once someone writes it in `moimio-saas`:

- **What the file is** and that it holds every event, archived ones
  included, plus the two reference lists.
- **That there is a command**, not twenty uploads, and a link to
  `docs/moving-a-workspace.md` for the exact steps.
- **What they will set up by hand** on the receiving server: accounts and
  passwords, per-event roles, webhook secrets, and email sending.

No CE code changes. The strings live in the hosted product, so they are not
part of STRINGS-1 either.

---

## LANG-1 — A default group type shows its stored English name inside the group type

**Status:** Open. Found by Johannes by hand on v1.0.4u in the German interface; established by the session 86 non-backup survey.

In German the Einteilung list showed a group type as **"Zimmerbelegung"**.
Opening that same group type showed the header **"Room Allocation"**. Both showed
the same 11 units, 58 assigned, 39 unassigned and 5 excluded, so it is one group
type wearing two names. "Room Allocation" is the stored name: a participant's own
data export shows `"category_name": "Room Allocation"` throughout.

**Cause.** `OrganiseDashboard.jsx:303` renders `{selectedCat.name}`, the stored
text. The list tile eight hundred lines below it, at `:600`, renders
`typeName(cat, t)`. The two are otherwise the same markup — both are
click-to-rename headings, both call `startInlineRename`, both carry the same
title attribute. Line 303 is simply the one that was missed when `typeName` came
in with v1.0.4. It is the only direct `.name` render in that file.

`typeName` (`frontend/src/utils/groupTypeLabel.js:20-24`) translates
`organise.default_type.<key>` while the row still carries a `name_key`, and
returns the stored text otherwise. The stored value for a default is the English
one, because that is what the seeder writes: `organise.default_type.rooms` is
"Room Allocation" in `en.json` and "Zimmerbelegung" in `de.json`. That is why the
two agree in English and disagree in German, and why this went unnoticed.

**A second site nobody had spotted.** `EventDetailPage.jsx:878` passes
`categoryName={topCat.name}` into `UnassignedBanner`, which renders it through
`banner.unassigned.title`. Same fault, different screen.

### Every other place a group type's name appears

| Surface | Renders | Right? |
|---|---|---|
| Einteilung list tile | `typeName` (`OrganiseDashboard.jsx:600`) | Yes |
| **Detail header** | `selectedCat.name` (`OrganiseDashboard.jsx:303`) | **No** |
| Manage-group-types list | `typeName` (`GroupTypesEditor.jsx:290`) | Yes |
| Participant insight panel | `typeName` (`InsightPanel.jsx:176`) | Yes |
| Reports panel and its PDF buttons | `typeName` (`ReportsPanel.jsx:359, 373, 383`) | Yes |
| Board dialogs, notes, clear-all confirm | `typeName` (`AllocationBoard.jsx:1288, 1885, 1988`) | Yes |
| PDF filename slug | `typeName` (`AllocationBoard.jsx:295`) | Yes |
| **"Closest to done" banner** | `topCat.name` (`EventDetailPage.jsx:878`) | **No** |
| The PDFs | `resolve_default_name(name_key, name, lang)` (`pdf_service.py:713`) | Yes |
| `participants.csv` "Excluded From" | stored name | Yes, by decision (v1.0.4v) |
| A person's data export | stored name | Yes — a data file, not a screen |
| The backup | stored name plus `name_key` | Yes |

**The PDFs need no separate handling.** `pdf_service.py:713` already resolves the
name inside `_build_pdf`, which all three renderers go through, and its own table
at `app/core/default_type_names.py` carries all six languages with
`tests/test_default_type_names.py` guarding it against drift.

### A stray write, found beside it

`OrganiseDashboard.jsx:180` compares the typed text against the **stored** name
(`trimmed === existing.name`) while the draft is seeded with the **translated**
one (`:175`, correctly). For a default group type those never match, so merely
clicking the header and clicking away fires a PATCH nobody asked for.

**It is not a data risk.** `update_category` (`allocation_service.py:168-184`)
asks `matches_default(current_key, incoming)`: if the incoming text is still one
of our own translations of that key, `name_key` survives untouched.
"Zimmerbelegung" is our German for `rooms`, so it matches and nothing is lost.
What remains is a needless database write on a stray click.

### An organiser can repair a lost key by hand today

Johannes's two English group types, "Rooms" and "Small Groups", are rows whose
`name_key` a pre-v1.0.4q restore dropped, which BACKUP-2 closed for future
restores. **Old rows can still be repaired from the interface.**
`allocation_service.py:181-184` restores a lost key on a **built-in**
(`is_default`) group type when the organiser types one of our current default
names in any language. So renaming it to exactly "Zimmerbelegung", or
"Room Allocation", or "방 배정", brings the key back and it starts translating
again. It must be exact, and it works only for the two group types an event is
born with — a group type the organiser created and happened to call "Rooms"
stays theirs, by design.

---

## LAYOUT-1 — Action rows that refuse to shrink push everything else off narrow screens

**Status:** Open. Found by Johannes by hand on v1.0.4u at about 780px on `/admin/webhooks`; the sweep is from the session 86 non-backup survey.

**What Johannes saw.** Wide, each endpoint shows its name, status badge,
address, subscribed event types and consecutive-failure count, with the action
buttons to the right. At about 780px the action buttons take the full width and
everything else is pushed out of view: four endpoints render as four identical
strips of buttons, with no name and no address.

**Cause.** `WebhooksPage.jsx:370` lays the row out as
`flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3`. The
information side is `min-w-0 sm:flex-1 overflow-hidden` (`:371`), which is
correct and will shrink. The button side is the fault:

```
<div className="flex flex-wrap gap-1 sm:justify-end sm:flex-shrink-0">   (:411)
```

`flex-shrink-0` on a `flex-wrap` container. As a flex item that refuses to
shrink, the group claims its full natural width — every button on one line — and
never gives any back. Because it never shrinks it never reaches the width at
which it would wrap, so the `flex-wrap` is inert. The information column, which
*is* allowed to shrink, is squeezed to nothing.

**Why about 780px.** Four buttons (`:412-425`) with long German labels —
"Test senden", "Zustellungen anzeigen", "Pausieren", "Secret erneuern" — need
roughly 470px of natural width at `text-xs`. At a 780px window the admin sidebar
is still shown, leaving a content column near 560px. The English build fails too,
just later. Note also that the `sm:` breakpoint is 640px for a layout that needs
about 900px.

### Every page that shares the fault, worst first

1. **`pages/WebhooksPage.jsx:411`** — the only occurrence of the exact
   anti-pattern, and the one confirmed by hand.
2. **`pages/BackupPage.jsx:97` and `:111`** — `flex items-center justify-between`
   rows whose text side is a bare `<div>` with **no `min-w-0`** and no
   truncation. One short button each, carrying `whitespace-nowrap` (`:102`), so
   the heading and hint text are what overflow. Degrades, does not disappear.
3. **`pages/UserManagementPage.jsx:160`** — `justify-between ... gap-3`, text
   plus one button, same missing `min-w-0`. Mild.

`EventDetailPage.jsx`, `EventsPage.jsx`, `RegistrationPhasePage.jsx` and
`SetupHub.jsx` all use `flex-wrap` on their `justify-between` rows and are fine.

**Unsettled by reading:** `components/BatchRegisterModal.jsx:453`, a four-column
`<table className="w-full text-xs">` inside a wrapper whose only overflow rule is
`overflow-hidden` (`:452`). The comment at `:449-450` says the layout collapses
to a sub-line on small screens, so it is probably fine. The experiment: open the
batch register preview at 400px with a long name in the data and see whether the
fourth column is clipped. Not run.

### The house already has a pattern, and these pages do not follow it

Two patterns, both already in use and both correct:

- **For tables.** A desktop-only table inside a scroll container plus a separate
  card list for phones: `<div className="hidden md:block overflow-auto
  max-h-[calc(100vh-20rem)]">` with `<table className="w-full min-w-max ...">`.
  Used verbatim at `PeopleTable.jsx:1259-1260` and `CheckInPanel.jsx:660-661`,
  and `CheckInPanel.jsx:657-659` names PeopleTable as the pattern it copies.
  `UserManagementPage.jsx:304` and `WebhooksPage.jsx` both wrap their delivery
  tables correctly — it is only the endpoint row that is wrong.
- **For rows.** `flex flex-col sm:flex-row` with `min-w-0` and `truncate` on the
  text side. `WebhooksPage.jsx:370-371` follows this and then breaks it with
  `sm:flex-shrink-0` on the other side.

Neither is written down anywhere. They live only as comments at
`PeopleTable.jsx:1256-1258` and `WebhooksPage.jsx:365-369`, which is why the next
action row will get it wrong again.

---

## EXCL-3 — The Excluded block wants one considered pass, not four patches

**Status:** Open, scheduled for v1.0.4x. Opened from the session 86 non-backup survey, at Johannes's request.

Four filed or found items are all about one block, and they pull against each
other: adding an (i) takes width from a row where names already truncate.
Johannes would rather have one considered pass than four separate patches.

- **EXCL-1** — no drag out of the block, click only.
- **EXCL-2** — names truncate beside the long undo label.
- **The card does not grow with its list** — on an event with 26 excluded people,
  expanding "Ausgenommen (26)" spilled the rows out past the card's white
  background. The panel-level half of this is closed with **PANEL-1** in
  v1.0.4w; the block-level half is here. `ExcludedBlock.jsx:60` is `shrink-0`
  and its expanded list at `:106` has no height cap and no scroll of its own, and
  the docked panel at `AllocationBoard.jsx:2146` has no `overflow-hidden` where
  the floating variant at `:2145` does.
- **No (i) on the row** — every other row on the board carries an (i) that opens
  the participant's panel; a row in the Excluded block has only the name and
  "Wieder berücksichtigen". Johannes's ruling: the (i) belongs there. Somebody
  excluded from one group type is still a participant of the event, and their
  history should not become unreachable because of it.

### The proposed pass

Change the row from *one line of three things* to *one line of two, with the
controls revealed on hover* — the idiom this screen already uses and names at
`AllocationBoard.jsx:2318-2321`, "the house idiom for a destructive write on a
chip is the hover-revealed, admin-gated icon button".

- **The name gets the whole row.** `truncate` stays, but with ~90% of 256px
  instead of ~55%.
- **Two icon buttons** grouped right, revealed on hover and focus (the row is
  already `group`, `ExcludedBlock.jsx:114`): the `ⓘ` copied verbatim from
  `AllocationBoard.jsx:2310-2317`, and an undo glyph carrying the **existing**
  `organise.exclude.undo_title` as its `aria-label` and `title`. On touch, where
  hover does not exist, both stay visible — the same `HAS_FINE_POINTER` test the
  board already uses.
- **The list scrolls inside the card.** A `max-height` of about 40vh plus
  `overflow-y: auto` on `ExcludedBlock.jsx:106`.

**This needs no new string.** The undo button already carries `aria-label` and
`title` set to `organise.exclude.undo_title` (`ExcludedBlock.jsx:126-127`), so
replacing the visible word with an icon costs no accessibility and invents no
key. `organise.exclude.undo` then falls out of use and can be deleted with
`prefs.scope` in the z release. The (i) reuses `insight.open`.

**Does the panel work for an excluded person as it stands? Yes.** Everything
`InsightPanel` shows is participant-scoped — contact details, registration,
assignments across all group types, notes and history — and none of it depends on
the person being eligible here. Their assignments in *this* group type will be
empty because excluding removed them, which is correct. Nothing about the
exclusion itself is shown; the history already records it.

### One decision this needs first

**Is EXCL-1 worth building, or should it be closed as won't-do?** The survey
recommends closing it. Unpicking the `stopPropagation` calls that make the block
a reliable drop target (`ExcludedBlock.jsx:66-79`) is what would be needed to let
a drag escape it, and the comment at `:20-25` records that a drop leaking through
to the panel behind "silently unassigns and looks like it worked" — a nasty
failure to reintroduce for a convenience. There are already two ways back, and
EXCL-1 is itself filed as "not because it blocks anything". **Not decided;
Johannes's call before v1.0.4x.**

---

## STREAM-2 — Cancelling or removing a participant does not reach the allocation board

**Status:** Open, scheduled for v1.0.4y. Found by the session 86 non-backup survey while settling STREAM-1, which does not reproduce.

There are three broadcast topics: `organise:<id>`
(`api/allocations.py:29-45`), `registration:<id>` (`api/participants.py:124`,
`:189`) and `checkin:<id>` (`api/participants.py:404`). The allocation board
subscribes to `organise` only (`AllocationBoard.jsx:405`).

`patch_participant` (`api/participants.py:276`) — which is how a participant is
**cancelled**, renamed, or has their gender or group code changed — publishes
**nothing**, on any topic. `delete_participant` (`:421`) publishes nothing
either. Counted by hand: zero `broker.publish` calls in each body.

So if one organiser cancels somebody on the People page, another organiser's
allocation board keeps them in the unassigned pool, keeps counting them in the
denominator, and keeps offering them for placement, until something unrelated
forces a refetch. That is a wider staleness window than the one STREAM-1
describes, and it is on the screen two people are most likely to be using at
once.

**The fix is two lines of backend.** Add
`await _publish_organise_change(event_id, "participant_changed")` to
`patch_participant` and to `delete_participant`. **No frontend change at all**,
because the board already refetches on any message
(`AllocationBoard.jsx:406-418`) and `loadAll` reloads the roster with it.

Worth doing in the same release as DASH-1 and DASH-3, because a stale roster and
a wrong denominator produce the same complaint from an organiser.

---

## OPS-1 — Detailed logging is the default, so ordinary running writes personal data to the log

**Status:** ✅ CLOSED in v1.0.4w (2026-09-18). Found by the session 86 non-backup survey, after Johannes noticed `import_all`'s own output buried in SQL logging.

`backend/app/core/database.py:14` sets `echo=(settings.log_level == "DEBUG")`,
so at `DEBUG` SQLAlchemy echoes every statement **with its bound parameters**.
The Python default in `core/config.py:26` is `INFO` — but nothing shipped that.
`docker-compose.yml:37` set `LOG_LEVEL: ${LOG_LEVEL:-DEBUG}` and
`.env.example:10` set `LOG_LEVEL=DEBUG`, so every self-hoster following the
install guide ran with statement logging on.

The consequence is not noise. Participant names, email addresses and dates of
birth were written to the container log on every request that touched them —
personal data in a place nobody thinks of as a data store, outside the retention
and erasure paths the rest of the product is careful about, and readable by
anyone who can run `docker compose logs`.

**Resolution.** Both defaults are now `INFO`. Detailed logging stays one
environment variable away for anyone who needs it, and `database.py` is
unchanged — the `DEBUG` behaviour is correct when somebody asks for it
deliberately.

Closed alongside **CE-2** (`uvicorn --reload` in the image), both being
production hygiene on the image self-hosters actually run.

See **SAAS-5** for the hosted side, which was checked and is not affected today.

---

## SAAS-5 — A tenant's log level is the control plane's log level

**Status:** Open. **Not this repo.** Found by the read-only hosted check in the v1.0.4w brief, session 86.

Checked and **not affected today**: the hosted control plane runs at `INFO`
(`~/dev/moimio-saas/.env:3`), its own default is `INFO`
(`app/config.py:18`), and `.env.example:5` is `INFO` too. So no tenant is
running with statement logging on.

The finding is the wiring, not the current value.
`app/provisioning/env_render.py:130` renders every tenant's `LOG_LEVEL` as
`settings.log_level` — **the control plane's own setting**, passed straight
through. So if an operator ever sets `LOG_LEVEL=DEBUG` on the control plane, for
their own debugging, every tenant provisioned from then on inherits it, and with
CE's `echo` behaviour (see **OPS-1**) that puts participant names, emails and
dates of birth into every one of those tenants' logs. One knob, two very
different consequences, and the second is invisible from where the knob is.

**What it wants:** a tenant log level that is its own setting, defaulted to
`INFO` and not derived from the control plane's. A constant would do; it does not
need to be configurable per tenant.

No CE code changes. Filed here so it is not lost, as SAAS-4 is.

---

## SHIP-1 — Publishing is automatic on a pushed version tag, and nothing said so

**Status:** Open until v1.0.5 ships. Established by the session 86 non-backup survey. **This is the ship procedure; read it before pushing anything.**

Nothing in this repository described what pushing does, and the assumption
carried in the session 86 briefs was that publishing images is a manual step.
**It is not.**

`.github/workflows/build.yml` is titled "Build and publish container images".
Its triggers (`:17-21`) are:

```
on:
  push:
    branches: [main]
    tags: ['v*']
  workflow_dispatch:
```

It logs in to GHCR (`:65-70`), builds `./backend` and `./frontend` (`:55-59`,
`:90-93`) and pushes to `ghcr.io/jc-universe87/moimio-backend` and
`-frontend` (`:14-15`). Tagging rules (`:81-83`): `sha-<short>` on every push,
`main` on a push to main, and **the tag's own name on a `v*` tag push.** A
`checks` job gates it (`:38-49`), running the i18n validator and the
version-marker check.

### What this means for the v1.0.5 ship

As of v1.0.4w there are **21 unpushed commits** and **17 unpushed tags**,
`v1.0.4h` through `v1.0.4w`. Every one of those tags is an intermediate
development release in one session's series. **None of them may ever be pushed
as a tag**, because each would publish two container images advertising a version
that was never a release — 34 images for work nobody outside this machine should
see.

**The rule, therefore: only `v1.0.5` may be pushed as a tag.**

The mechanic that protects this, and the one that does not:

- `git push origin main` does **not** push tags. It is safe, and it fires one
  verification build tagged `sha-<short>` and `main`, which is harmless.
- `git push --tags` and `git push --follow-tags` would send all seventeen and
  fire seventeen release builds. **Neither may be used on this repository.**

If the intermediate tags are ever wanted on the remote for the record, the
workflow would have to be taught to ignore them first. That is not worth doing.

Close this entry when v1.0.5 has shipped and the rule has been written into
whatever release checklist replaces it.
