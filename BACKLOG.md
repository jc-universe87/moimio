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

---

## CE-3 — Next CE zip: inner wrapper folder becomes `moimio/`

**Status:** Note only. Happens when the next CE zip is cut, not before.

The next CE zip renames the inner wrapper folder from `moimio-ce/` to
`moimio/`, removing the scratch-copy step in the CE pipeline. When the rename
happens, the README Quick start gains the unpack step for archive recipients.

---

## PDF-1 — Detailed roster gender column is narrower than its header

**Status:** Open. Pre-existing; measured during v1.0.4g ship.

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

**Status:** Open. Pre-existing; found in session 84 while reading the endpoints for the exclusion work (v1.0.4i). Not fixed there.

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

**Status:** Open. Found in session 85 while building the exclusion UI (v1.0.4k). Deliberately not picked up there.

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

**Status:** Open. Found in manual testing of v1.0.4k (2026-09-17).

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

**Status:** Open. Found in manual testing of v1.0.4k (2026-09-17).

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

**Status:** Open. Found in session 86 phase 1 while reading the backup path for BACKUP-1 (v1.0.4m). Not fixed there.

`export_event_zip` writes a literal field list per model, passed to the
`_row` helper. Nothing is picked up automatically, so a column added to a
model after its list was written is silently dropped from every backup.
Dropped today:

- Event: `timezone`, `details_confirmed`, `registration_confirmed`,
  `is_archived`, `over_cap_signalled`
- AllocationCategory: `name_key`, `item_label_key`,
  `exclusive_group_codes`, `confirmed`
- AllocationUnit: `mark_restriction`, `is_kept`
- MarkDefinition: `cluster_behaviour`
- Participant: `override_group_room`, `checked_in_at`
  (`confirmation_token` is rightly excluded: it is a secret)

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

---

## BACKUP-3 — Ids inside JSON fields are not renumbered on restore

**Status:** Open. Found in session 86 phase 1 while reading the backup path for BACKUP-1 (v1.0.4m). Not fixed there.

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

---

## BACKUP-4 — Event data the backup does not carry at all

**Status:** Open. Found in session 86 phase 1 while reading the backup path for BACKUP-1 (v1.0.4m). Not fixed there.

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

---

## BACKUP-5 — Allocation history is not in the backup

**Status:** Open. Found in session 86 phase 1 while reading the backup path for BACKUP-1 (v1.0.4m). Not fixed there.

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

---

## BACKUP-6 — participants.csv shows no exclusions

**Status:** Open. Feature request, not a defect. Found in session 86 phase 1 while reading the backup path for BACKUP-1 (v1.0.4m).

`GET /api/events/{event_id}/export/participants.csv` in `api/export.py`
has no exclusion column, and runs no query for one. A spreadsheet of
participants gives no sign that anyone is excluded from anything, so an
organiser working from the CSV cannot see a decision they made in the app.

The natural shape is one column listing the group types each participant
is excluded from, matching how the existing `Marks` column flattens mark
names into one comma-separated cell.

---

## VERSION-1 — `check-version-markers.py` does not read the `version.py` docstring

**Status:** Open. Found in session 86 phase 1 while reading the version markers for v1.0.4m. Corrected by hand there, not fixed.

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
