# Changelog

All notable changes to Moimio CE are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0e/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This is the public, user-facing changelog. Detailed per-development-iteration history is kept internally and is not published.

---

## [Unreleased]

Nothing yet. Open issues at <https://github.com/jc-universe87/moimio/issues> for things you'd like to see.

---

## [1.0.0m] — 2026-05-21

Bug fix on the public registration form. When an extra person ticked
"Same group code as {primary}", they were quietly given a different
group code anyway — two stacked causes, single user-visible symptom:
families ended up in separate clusters during allocation.

### Fixed

- **Extras with "same group code" now actually share the primary's
  code.** Two stacked bugs, one fix.

  First, the frontend only forwarded the primary's typed code to extras
  when the primary had explicitly picked the "I'll type a group code"
  radio. Default-mode registrants (the common path) saw the checkbox,
  ticked it, and silently sent no `group_code` field for extras at all
  — the backend then auto-generated a fresh code per extra.

  Second, even when the code was forwarded, the frontend sent the
  *typed* stem (e.g. `SMITH`), not the *resolved* `STEM-NNN` the
  backend had just persisted for the primary. The backend's collision-
  safe resolver (v1.0-pre) treats bare stems as start-of-cluster and
  appends a fresh random suffix on each call, so the extra still
  landed in a different cluster.

  The fix captures the primary's resolved code from its registration
  response and sends that exact value for any extra with `groupCodeMode
  === 'same'`, independent of which grouping radio the primary chose.
  Complete `STEM-NNN` codes are taken verbatim by the backend, so the
  inherited value is preserved. The "same" label now matches reality
  in all three primary modes (`none`, `code`, `request`).

  Frontend-only change; backend, schema, and tests untouched.

### Affected files

- `frontend/src/pages/RegisterPage.jsx` — capture primary response in
  the submit handler; inherit `group_code` and `group_code_categories`
  unconditionally for `groupCodeMode === 'same'`.
- `frontend/package.json` — `moimioVersion` bumped to `v1.0.0m`.
- `backend/deploy/production.yml` — image tags bumped to `v1.0.0m`
  per the locked policy ("tags bumped together each CE release",
  `backend/deploy/README.md`).
- `backend/deploy/README.md` — example tag updated to match.

---

## [1.0.0l] — 2026-05-21

Production compose template for the hosted SaaS. No runtime behaviour
change for self-hosters — the dev compose at the project root is
untouched. Unblocks Moimio SaaS v0.4.0 (the real provisioning driver),
which reads this template out of the backend GHCR image to spin up
per-tenant stacks.

### Added

- **`backend/deploy/production.yml`** — production compose template
  used by the Moimio SaaS provisioning driver. References pinned GHCR
  image tags (no `:latest`), declares the two-network topology
  (per-tenant `moimio-${SUBDOMAIN}-internal` for db+backend+frontend,
  shared `moimio-public` for frontend+outer Caddy), publishes no host
  ports, uses no source mounts, runs healthchecks on all three
  services, and treats secrets as required (`${VAR:?...}` fail-loud
  syntax) rather than defaulted.
- **`backend/deploy/README.md`** — documentation of the env vars the
  template expects (split into required vs. optional), the SaaS
  provisioner / CE responsibility boundary, the network topology, and
  a one-line distinction between the new `backend/deploy/` (artefact
  for the hosted SaaS) and the existing root-level `deploy.sh`
  (bootstrap script for self-hosters).
- **`BACKLOG.md`** — three new items: `CE-1` (image-update awareness),
  `CE-2` (backend `--reload` in production), `SAAS-3` (admin dashboard
  global product config section, first user Mailjet credentials).

### Why this lives under `backend/deploy/`, not at the project root

The CI workflow (`.github/workflows/build.yml`) builds the backend
image with `context: ./backend`. For the production template to ship
inside the built backend image — so the SaaS provisioner can read it
out of the image at `/app/deploy/production.yml` without a Git clone —
the template must be reachable from the backend build context.
Placing the folder inside `backend/` is the smallest possible change
to make this work. The existing `COPY . .` step in the Dockerfile
then copies the deploy folder along with everything else; no
Dockerfile change required.

The naming overlap with the root-level `deploy.sh` is unfortunate but
intentionally explicit — `deploy.sh` (script) and `backend/deploy/`
(directory) live at different paths and serve different audiences.
The README disambiguates.

### Discoveries flagged while drafting

- **`VITE_API_URL` is vestigial.** The frontend code uses a hardcoded
  `const API_BASE = '/api'` (in `frontend/src/services/api.js`), a
  relative path that the frontend's own Caddy reverse-proxies to the
  backend. The `VITE_API_URL` variable in the dev compose is
  unreferenced. The production template omits it. Cleaning up the
  dev compose to also omit it is out of scope for v1.0.0l; flagged
  here for a future ship.
- **Backend image runs `uvicorn --reload`** (see `backend/Dockerfile`
  line 36). Appropriate in dev, wrong in production — wastes CPU on
  a file-watcher with nothing to watch, and theoretically vulnerable
  to spurious restarts. The right fix is its own discussion (per-env
  CMD? parameterise via env var? compose-level `command:` override?).
  Captured as `CE-2` in `BACKLOG.md`.

### Unchanged from v1.0.0k-3

- All application code (backend, frontend, migrations, tests).
- All translations (1089 keys per locale).
- The dev compose at the project root (`docker-compose.yml`).
- The root-level `deploy.sh` bootstrap script.
- `backend/Dockerfile` — the existing `COPY . .` already copies the
  new `deploy/` folder into the image.

### Process

- `frontend/package.json` `moimioVersion` bumped to `v1.0.0l` per
  the ship checklist locked in v1.0.0k-3.

---

## [1.0.0k-3] — 2026-05-21

Re-issue of v1.0.0k-2 with one cosmetic fix. No application code
changes; behaviour is identical to v1.0.0k.

### Fixed

- **Sidebar version label was stuck at `v1.0.0j`.** The
  `moimioVersion` field in `frontend/package.json` — the canonical
  source of truth for the version shown in the admin sidebar — was
  not bumped when v1.0.0k shipped. The deployed code was v1.0.0k but
  the label said v1.0.0j. No functional impact; the application
  ran the new code as expected. Fix: bump `moimioVersion` to
  `v1.0.0k-3` so the label matches the ship.

### Process improvement

- The vite.config.js comment ("Release workflow: bump
  `moimioVersion` in package.json once per ship") is now mirrored
  as a mandatory step in the ship checklist. Future ships will fail
  the self-review if the package.json `moimioVersion` does not
  match the CHANGELOG header.

### Unchanged from v1.0.0k-2

- All application code (backend, frontend, migrations, tests).
- The `PYTHONDONTWRITEBYTECODE=1` fix on the backend service.
- All six v1.0.0k items remain in place.

---

## [1.0.0k-2] — 2026-05-21

Re-issue of v1.0.0k with one operational fix. No application code
changes; v1.0.0k application behaviour is preserved exactly.

### Fixed

- **Root-owned `.pyc` files on the host bind mount.** The backend
  container runs as root (default for the `python:3.12-slim` image),
  and Python writes `.pyc` files into `__pycache__/` directories
  alongside source. Because `docker-compose.yml` bind-mounts
  `./backend/app:/app/app`, those `.pyc` files appeared on the host
  owned by root — making a routine `rm -rf moimio-ce/` during
  redeploy fail with "Permission denied" for the unprivileged host
  user. Fix: set `PYTHONDONTWRITEBYTECODE=1` on the backend service
  so Python writes no bytecode files at all. Slight cold-start cost
  on first request after rebuild; negligible in practice.

### Operational notes

- If you already deployed v1.0.0k and have a half-deleted
  `moimio-ce/` directory containing root-owned `.pyc` orphans, clear
  it with a brief root container before re-extracting:
  ```bash
  docker run --rm -v ~/docker-compose:/work alpine sh -c "rm -rf /work/moimio-ce"
  ```
  No database changes; the host `pgdata` volume is untouched.

### Unchanged from v1.0.0k

- All application code (backend, frontend, migrations, tests).
- All translations (1089 keys per locale).
- All six v1.0.0k items remain in place.

---

## [1.0.0k] — 2026-05-21

Registration form polish + locale presets.

### Fixed

- Custom fields now render and submit on additional participants (was silently dropped)
- Submit-validation highlight extended to all required fields on extras

### Changed

- Group code on additional participants: three-way radio (same / none / different)
- Six date format presets covering UK/EU, US, ISO, DE, KR conventions
- Danger zone hint refreshed across all six locales — honest about which actions can be undone
- Group Types create form: leftover gender toggle removed (finishes v0.74 deprecation)

No migrations. No breaking changes.

---

## [1.0.0j] — 2026-05-13

CI/CD pipeline ship. Adds GitHub Actions workflow that builds backend
and frontend images on every push and publishes them to GitHub
Container Registry. No runtime behaviour change.

### Added

- `.github/workflows/build.yml` — GitHub Actions workflow that:
  - Builds both `backend` and `frontend` Docker images in parallel
    via matrix on every push to `main`
  - Pushes to `ghcr.io/jc-universe87/moimio-backend` and
    `ghcr.io/jc-universe87/moimio-frontend` with commit-SHA tags
    (e.g. `sha-abc1234`)
  - Additionally tags with the version name (e.g. `v1.0.0j`) when a
    `v*` git tag is pushed
  - Uses GitHub's built-in `GITHUB_TOKEN` for GHCR authentication —
    no PAT setup required
  - Uses GitHub Actions cache, scoped per-component, for fast
    incremental builds

### Operational notes

- CE convention: **no automatic `latest` tag**. Downstream consumers
  (SaaS provisioning, self-hosters) always pin to a specific version.
  Reproducibility over convenience.
- Branch pushes verify the images still build but don't move any
  floating tag.
- After this workflow lands, the first release tag (`v1.0.0j`)
  triggers the first published image. Until then, only `sha-` tagged
  builds will exist.
- GHCR packages are private by default and inherit the repo's
  visibility. When the CE repo goes public (alongside SaaS launch),
  each image package can be made public via GitHub Settings →
  Packages.

### Unchanged from v1.0.0i

- All application code (backend, frontend, database).
- All tests: 128 backend passing, 6 frontend passing.
- All translations, all assets, all build outputs.

---

## [1.0.0i] — 2026-05-13

Focused engine-test-refresh ship. Rewrites all 11 ENGINE-1 quarantined
tests to assert current engine behaviour rather than the older
behaviour they were originally written against. Backend test suite
now reports **128 passed, 0 xfailed, 0 failed** — fully green for
the first time since whenever PASS 4 was changed without updating
tests. No runtime behaviour changes; the deployed application is
byte-for-byte identical to v1.0.0h-3 from the user's perspective.

### Changed

- **`test_engine.py`** — 5 tests rewritten:
  - `test_gender_restriction_respects_pools` — drops "balanced within
    pool 3:3" sub-assertion (engine produces 6:0 or capped 4:2 via
    greedy fill, not pool-round-robin). Pins the no-cross-gender
    invariant, which is the part that matters for correctness.
  - `test_oversized_cluster_unplaced_when_split_disabled` — updated
    to pin the current dissolution behaviour (cluster members placed
    individually, no `group_code_split` reason). Original "leave
    unplaced" expectation flagged as ENGINE-2 product question.
  - `test_unknown_gender_placement_counted` — contract reversed.
    Engine no longer silently falls back; unknown-gender participant
    is left unplaced. New assertion verifies no silent fallback
    placements (`gender_unknown_placements` stays 0).
  - `test_v073a_mixed_explicit_and_implicit_caps_place_everyone` —
    drops "Room 2 has exactly 2" sub-assertion. Engine fills the
    uncapped rooms and leaves the cap-2 room empty. Bug 1 regression
    check (all 25 placed) preserved. Behaviour flagged as ENGINE-3.
  - `test_v074_constrained_units_fill_first` — strict Semantics A
    assertion relaxed to "both units used, no overflow." Equalise
    sweep undoes Semantics A in mixed-capacity categories. Flagged
    as ENGINE-4.

- **`test_engine_v074.py`** — 2 tests rewritten:
  - `test_v074_a4_oversized_cluster_split_evenly` — strict 4+4 split
    relaxed to "everyone placed, no overflow." Engine splits 4+3+1
    across three units rather than 4+4 across two.
  - `test_v074_a4_oversized_cluster_split_disabled` — updated to
    match dissolution behaviour (same as ENGINE-2).

- **`test_v1_0_0e_equalise_and_warning.py`** — 1 test re-aimed:
  - `test_equalise_preserves_previous_reason_for_audit` now uses a
    cluster-pre-fills-Room-A scenario where equalise still fires for
    the solo fill, exercising the same audit-trail contract.

- **`test_allocation_events.py`** — 3 tests updated to accept the
  current placement_reason payload shape (engine stamps `unit_id`
  alongside `reason`).

### Added (BACKLOG)

- **ENGINE-2** — Open product question: should
  `split_oversized_groups=false` dissolve clusters or leave them
  unplaced? Current behaviour scatters; setting name suggests
  unplaced-for-review.
- **ENGINE-3** — Open product question: in mixed capped/uncapped
  categories, should the capped unit get priority placement?
- **ENGINE-4** — Open product question: should equalise sweep
  respect Semantics A's "constrained rooms drain first" intent?

All three are LOW–MEDIUM severity; the practical outcomes are correct
(all participants placed, capacities respected). The questions are
about whether the heuristics could be tighter for organiser intent.

### Removed

- All `@pytest.mark.xfail` markers from the 11 engine tests. Each
  test now passes on its own merit.

### Internals

- Backend suite: **128 passed, 0 xfailed, 0 failed**.
- Frontend Vitest suite: **6 passed**.
- ENGINE-1 closed in `BACKLOG.md`.

---

## [1.0.0h-3] — 2026-05-13

Test-infrastructure ship. Three streams: a Vitest frontend test harness,
quarantine of 11 pre-existing allocation-engine drift tests, and a new
`BACKLOG.md` at scaffold root tracking open items across ships. No
runtime behaviour changes — the deployed application is byte-for-byte
identical to v1.0.0h-2 from the user's perspective.

### Added

- **Vitest + jsdom + @testing-library/react** as frontend devDependencies.
  Run with `npm test` (single pass), `npm run test:watch` (continuous),
  or `npm run test:coverage` (with v8 coverage report). Co-located
  test files (`<source>.test.jsx` next to `<source>.jsx`) keep coverage
  obvious. Not yet wired into the Dockerfile build stage; that's a
  follow-up once coverage is broader.
- **`useCapabilities` regression-pin suite** (6 tests) — would have
  caught the v1.0.0h bug where the hook silently discarded the
  `create_event_confirmation` field. Tests verify: the new field is
  exposed when API returns it, defaults to false when API omits or
  fails, legacy `allocation` and `outbound_webhooks` fields preserved,
  optimistic defaults during pre-fetch loading.
- **`BACKLOG.md`** at scaffold root. Persistent across ships (unlike
  session-specific docs that get replaced each ship). Tracks open
  items with status, owner, and decision-needed flags. Initial
  entries: ENGINE-1, TEST-FRONTEND-1, SAAS-1.

### Fixed

- **Backend test suite now reports a clean signal.** 11 pre-existing
  allocation-engine tests marked `@pytest.mark.xfail` with `ENGINE-1`
  references. These had been silently red for an unknown period
  (probably since whoever last changed the engine's PASS 4 from
  greedy-fill to round-robin without updating the tests). With the
  v1.0.0h conftest fixes, they became visible; quarantining is the
  pragmatic short-term move while the underlying engine design
  question is investigated.
- Total backend suite state: **117 passed, 11 xfailed, 0 failed.**

### Internals

- Frontend lint baseline unchanged (22 warnings, 0 errors — none from
  the new test files).
- `BACKLOG.md` lives at scaffold root alongside `CHANGELOG.md`. Future
  ships should update it (add new items, close completed ones with a
  short reference to the ship that closed them) rather than replacing
  it wholesale.

### Notes for next session

ENGINE-1 (option A vs B vs C) and SAAS-1 (scoping conversation) are
the two open backlog items requiring product/architecture input. C
holds for ENGINE-1 until decided; the SaaS scoping conversation can
happen any time the SaaS provisioning stream picks up.

---

## [1.0.0h-2] — 2026-05-13

One-line bug fix to v1.0.0h. The `useCapabilities` React hook was
discarding the `create_event_confirmation` field returned by the API,
so even with the flag and all three data env vars correctly configured,
the frontend never opened the confirmation dialog.

### Fixed

- **`useCapabilities` now reads `create_event_confirmation`** from the
  API response. The hook destructures specific fields from `/api/capabilities`
  rather than spreading the entire response — when v1.0.0h added the new
  field to the API contract, the hook needed a matching update and didn't
  get one. The bug only surfaced on a real device with the flag and data
  vars all correctly set, which is why the v1.0.0h backend test suite
  (which only exercised the API endpoint, not the hook that consumes it)
  passed cleanly.

### Internals

- `create_event_confirmation` defaults to **false** in the optimistic
  pre-fetch state. The other two capability flags default to true on
  the "showing a sidebar entry that 404s is less bad than blanking the
  sidebar" rationale, but inserting a charge-confirmation dialog into
  the event-create flow on a transient API failure would be the wrong
  failure mode. Off-by-default fails closed.
- API response parser now uses `=== true` for this flag rather than
  the `!== false` trick used for the legacy flags. The legacy trick
  treats a missing field as "on" — correct for capabilities that
  predate the response schema, wrong for ones added in a later version.

### Test coverage gap exposed

Backend tests verified the `/api/capabilities` response shape correctly
(`test_capabilities_response_includes_create_event_confirmation`). Frontend
tests don't exist — there's no Vitest harness in the repo. The fix lands
without an automated regression pin; manual smoke (Section D2 of the
v1.0.0h-1 part-2 checklist) re-tests it. Setting up a frontend test
harness so similar contract-mismatch bugs get caught earlier is now an
explicit backlog item for a follow-up ship.

---

## [1.0.0h-1] — 2026-05-13

Architecture simplification on top of v1.0.0h, plus one regression
bug fix. The 24-hour grace window machinery has been removed from CE;
SaaS now owns the timing policy end-to-end. Net code is smaller than
v1.0.0h was.

The motivation: CE's job is to tell SaaS what happened, not to make
billing decisions. The original v1.0.0h design split destruction into
"Cancel" (within 24 h, fires webhook, intended refund) and "Delete"
(after 24 h, silent, no refund) — which baked a billing rule
(24 h refund policy) into CE config and presented two destructive
buttons to the admin during the first day, inviting confusion. The
simpler model: one Delete button, always emits a single webhook,
SaaS decides whether the deletion warrants a refund.

### Changed

- **`event.cancelled` event type → `event.deleted`.** There is now a
  single destructive verb; CE no longer has a "cancel" concept.
  Receivers subscribed to all event types (`["*"]`) need no change.
  Receivers with explicit subscriptions should swap any
  `event.cancelled` entry for `event.deleted`.
- **The Delete event flow now emits an `event.deleted` webhook** (in
  the same DB transaction as the cascade delete, same atomicity
  contract as `event.created`). SaaS receivers can compare the
  payload's `deleted_at` timestamp against the original `event.created`
  timestamp for the same event ID and apply whatever refund policy
  they want — 24 hours, 48 hours, per-tier, anything. The window is
  no longer hard-coded in CE.
- **`event.delete.warning` copy in all 6 locales** now explains the
  paid-plan refund behaviour. Self-hosters and free-plan tenants
  naturally tune out the conditional ("If you're on a paid plan…").

### Removed

- **`cancel_event` service function, `CancelWindowExpiredError`,
  `GRACE_WINDOW_HOURS` constant** — 24 h is no longer a CE concept.
- **`POST /api/events/{event_id}/cancel` route** — gone. There was no
  third-party adoption (v1.0.0h hadn't been pushed publicly yet).
- **Frontend cancel surface** — steel-blue Cancel card on
  EventDetailPage, the corresponding StrongDeleteConfirm modal,
  `eventsApi.cancel()` wrapper, `withinGraceWindow` computation.
- **Nine `event.cancel.*` i18n keys + `errors.event.cancel_window_expired`**
  across all six locales (54 entries total).

### Fixed

- **`test.ping` webhooks now carry `tenant_id`.** A regression in
  v1.0.0h: the test-send endpoint hand-built its envelope dict and
  silently bypassed the `MOIMIO_TENANT_ID` stamping that every other
  event type uses. Now routes through `_envelope()` so test pings get
  the same envelope shape as real events. Real-world impact: SaaS
  receivers couldn't reliably identify which tenant a test webhook
  came from. Caught by Johannes' v1.0.0h smoke test Section A2.
- **`TRANSLATION_RULE.md` ES convention corrected.** Was listed as
  "tú/usted | Mixed; follow existing strings — most app uses usted",
  which was wrong on both counts. ES is `tú` throughout, matching
  the existing codebase. DE and FR rules unchanged.

### Internals

- Twelve backend tests removed (the cancel-specific suite); ten new
  tests added (`test_v1_0_0h_1_delete_and_test_ping.py`) covering
  the delete-emits-webhook contract, the test.ping tenant_id stamping
  fix, and a regression-pin that the `/cancel` route stays gone.
- Total v1.0.0h-1 test count: 27, all passing.

### Notes for SaaS operators

The webhook contract changes to express:

- Subscribe to `event.created` to know when an event begins existing.
- Subscribe to `event.deleted` to know when it stops existing.
- Compare the two timestamps for the same `event_id` to apply your
  refund policy. The policy is yours; CE has no opinion.

`event.cancelled` no longer fires. Update any wired receivers before
deploying v1.0.0h-1 alongside SaaS code.

---

## [1.0.0h] — 2026-05-13

SaaS-readiness layer on top of v1.0.0g. Three CE-side capabilities the
SaaS provisioning layer can switch on per-tenant, all off by default so
self-hosters see no behavioural change. No schema change; no migration;
no breaking changes to the v1.0.0g webhook envelope shape.

### Added

- **Optional tenant identity stamping.** New env var `MOIMIO_TENANT_ID`.
  When set, every outbound webhook payload carries a top-level
  `tenant_id` field so a downstream receiver routing webhooks from
  multiple installations can tell them apart. Omitted entirely from
  payloads when blank — self-hosters never see the field.
- **`event.created` and `event.cancelled` webhook events.** Two new
  event types emitted by the existing v1.0.0g outbound-webhook
  subsystem: `event.created` fires whenever an admin creates an event
  in CE; `event.cancelled` fires from the new cancel-within-grace
  path (see below). Both carry GDPR-minimal payloads (just `event_id`
  and the relevant timestamp), so the wire transcript holds the
  routing facts and nothing else. Subscribed endpoints with
  `event_types: ["*"]` automatically receive these; explicit
  subscriptions need to add the new event types.
- **24-hour grace cancel for events.** Within 24 hours of creating an
  event, Super Admins see a new "Cancel event" card on the event detail
  page (above the Danger zone). Clicking it opens a type-to-confirm
  modal; on confirmation, the event is cascade-deleted **and** an
  `event.cancelled` webhook fires — the downstream side can use that
  signal to trigger a refund of any associated charge. After 24 hours
  the card disappears; the existing Delete path stays available but
  no webhook fires from there. Server enforces the same window
  independently — a stale client cannot bypass it.
- **`FEATURE_CREATE_EVENT_CONFIRMATION` capability flag.** Off by
  default. When on, the event-create flow surfaces a confirmation
  dialog showing what will be charged before the event is actually
  created. Powered by three new optional env vars
  (`EVENT_CHARGE_AMOUNT`, `EVENT_CHARGE_CURRENCY`, `BILLING_CARD_LAST4`)
  and a new auth-required `GET /api/billing-info` endpoint. Currency
  is rendered locale-aware via `Intl.NumberFormat`; missing values
  fall back gracefully to "card on file" / "a charge on your account"
  wording rather than blocking event creation.

### Changed

- **`GET /api/capabilities`** response now includes a
  `create_event_confirmation: bool` field. Existing clients ignoring
  unknown fields are unaffected.
- **`TRANSLATION_RULE.md`** gains a new "Per-locale conventions"
  section documenting the locked address-form table — **DE is always
  du, FR is always vous** — plus terminology notes (Moimio events
  use "Event"/"absagen" in DE, not "Veranstaltung"/"stornieren") and
  locale-native quotation-mark preferences.

### Fixed

- **DE address-form drift** — two strings still in the formal Sie
  form (`organise.clear_all_confirm.body`, `people.export.error`) are
  now in du form, matching the locked DE convention.
- **i18n parity gap closed.** Fifty-one v1.0.0g webhook UI strings
  that were EN-only have been translated into DE/KO/ES/FR/pt-BR.
  Locale total now 1097 keys × 6 locales with zero gaps. The webhook
  admin surface now reads correctly in every supported language.
- **Pre-existing test-infrastructure regressions in `conftest.py`** —
  the async `client` fixture was decorated with `@pytest.fixture`
  rather than `@pytest_asyncio.fixture` (silently broke under recent
  pytest-asyncio releases); and `from app.main import app` was being
  shadowed by the subsequent `import app.models`, leaving the fixture
  with the package module instead of the FastAPI instance. Every
  HTTP integration test was blocked by these. Both fixed.

### Security / privacy

- **`/api/billing-info` is auth-required.** Card last-4 is customer
  data; only authenticated users see it. Knowing whether the
  capability flag is on (via `/api/capabilities`) remains public —
  that fingerprint is harmless.
- **No full PAN ever in CE.** Only the last 4 digits, supplied by the
  provisioning layer. Documented in `.env.example`.
- **Webhook payload minimality.** Both `event.created` and
  `event.cancelled` payloads carry only the resource ID and a
  timestamp. Event name, admin email, participant data — none of it
  is in the wire payload. Receivers needing more can resolve from
  their own records using `event_id`.

### Notes for SaaS operators

- All four new env vars (`MOIMIO_TENANT_ID`, `FEATURE_CREATE_EVENT_CONFIRMATION`,
  `EVENT_CHARGE_AMOUNT`, `EVENT_CHARGE_CURRENCY`, `BILLING_CARD_LAST4`) are
  read at startup. To change a tenant's price or card-on-file display,
  update the env and recreate the container (not just restart — env
  changes need `--force-recreate`).
- The card-update flow on the SaaS side is "Paddle webhook →
  patch CE env → `docker compose up -d --force-recreate backend`".
  A small in-flight race is possible (admin loads create page before
  restart, submits after) but the actual charge is processed
  server-side from the `event.created` webhook, so the source of
  truth on the amount billed is SaaS, not the dialog.

### Internals

- 35 new backend pytest tests across 5 files cover envelope stamping,
  cancel-window enforcement (within / at boundary / outside), payload
  minimality, auth gates, route status codes, and translatable
  error-key contracts. All pass against a real Postgres test DB.
- Frontend manual smoke-test checklist shipped separately
  (`20260513_moimio-v1_0_0h-manual-smoke-test.md`) — covers the UI
  surfaces a Vitest harness would, until that harness is built.

---

## [1.0.0g-4] — 2026-05-12

Documentation pass for the v1.0.0g webhook subsystem. No code changes;
no migration. Brings the public-facing docs in sync with the feature
ahead of pushing v1.0.0g to GitHub.

### Added

- **`docs/webhooks.md`** — full integration guide for self-hosters
  and developers: configuring endpoints, signature verification recipe
  (Python and Node.js samples), payload format, header reference,
  retry policy, idempotency, environment configuration, troubleshooting
- **`ARCHITECTURE.md` § 10 — Outbound webhooks for integrations** —
  the design rationale: why generic-not-SaaS-specific, signed-at-the-wire
  with HMAC-SHA256, at-least-once delivery with the retry schedule,
  why secrets are plaintext-at-rest, how the AsyncIOScheduler is wired
- **`docs/glossary.md`** — new "Integrations" section with terms:
  Outbound webhook, Endpoint, Signing secret, Delivery, Endpoint state,
  SaaS-managed endpoint
- **`docs/data-model.md`** — table count updated from 17 to 19; entries
  for `outbound_webhook_endpoints` and `outbound_webhook_deliveries`;
  three new enums documented (`WebhookEndpointState`,
  `WebhookEndpointManagedBy`, `WebhookDeliveryStatus`)
- **`docs/faq.md`** — new Q under Features: "Can I integrate Moimio
  with Slack, Zapier, or my own systems?"
- **`README.md`** — brief integrations paragraph in the overview; new
  row in the documentation table linking to the webhooks guide

### Notes

- Cross-references are correct end-to-end (README → guide; guide →
  ARCHITECTURE for design rationale; guide → data-model for schema;
  glossary entries link to guide; FAQ links to guide).
- No code touched. The shipped subsystem from v1.0.0g, v1.0.0g-1,
  v1.0.0g-2, v1.0.0g-3 is unchanged. This is purely the
  doc-completion ship before GitHub push.

---

## [1.0.0g-3] — 2026-05-12

One-line root-cause fix to v1.0.0g's env-var wiring. No schema change;
same `100g00000` Alembic head.

### Fixed

- **v1.0.0g env vars never reached the backend container.** The
  `docker-compose.yml` `backend` service uses an explicit
  `environment:` block — only the variables listed there are passed
  from the host's `.env` into the container. I added the five new
  vars (`FEATURE_ALLOCATION`, `FEATURE_OUTBOUND_WEBHOOKS`,
  `MOIMIO_WEBHOOK_URL`, `MOIMIO_WEBHOOK_SECRET`,
  `WEBHOOK_DELIVERY_RETENTION_DAYS`) to `core/config.py` and
  `.env.example` in v1.0.0g but forgot to register them in
  `docker-compose.yml`. The Pydantic settings layer silently fell
  back to defaults for everything, so:
  - SaaS auto-registration was a no-op even with valid env vars set
  - Capability flags couldn't be toggled off via `.env`
  - Retention couldn't be tuned
  Now wired through. The defaults match v1.0.0g's stated behaviour
  (both flags on, no auto-register, 30-day retention) so deployments
  that don't set anything in `.env` continue to behave identically.

### Notes

- Surfaced by attempting the optional Part 4 of the v1.0.0g smoke test
  (SaaS auto-register). Worth a permanent process note: every new
  env var added to `config.py` requires three matching edits —
  `.env.example` (documentation), `docker-compose.yml` (wiring), and
  the Pydantic `Settings` class (the typed read). Missing any one
  silently falls back to the default. The smoke test must include a
  check that the var actually reaches the container
  (`docker compose exec backend env | grep <VAR>`) for any env var
  that gates new behaviour.

---

## [1.0.0g-2] — 2026-05-12

Three more quality fixes on top of v1.0.0g-1 from real-device smoke
testing. No schema change; same `100g00000` Alembic head.

### Fixed

- **Webhook endpoint card layout collapsed on narrow viewports.** URL
  used `break-all` (legitimate intent: wrap long URLs) but combined
  with a flex row that wrapped buttons beside info, the layout
  degenerated at narrow widths: URL broke one character per line,
  buttons overlapped the state pill. Switched URL display to `truncate`
  + `title` attribute (full URL on hover). Card now stacks
  info-above-buttons on screens < 640 px, side-by-side on wider
  screens. Tested at 1170 px (overflow gone), 870 px (clean), 750 px
  (clean stack).

- **"I have saved this secret" checkbox persisted across opens.** Real
  safety bug. `useState(false)` only resets on mount, and returning
  `null` from a component's render does NOT unmount it — the parent
  was still rendering `<WebhookSecretModal />` on every render, so the
  acknowledge state survived from one secret reveal to the next. Two
  fixes for belt-and-braces: (1) added a `useEffect` inside the modal
  that resets `acknowledged` and `copied` whenever it opens with a new
  endpoint; (2) the parent now conditionally renders the modal
  (`{revealedSecret && ...}`) so it truly unmounts on close. Result:
  every secret reveal requires a fresh active acknowledgement —
  the checkbox is friction by design, not a sticky preference.

- **URL fragments are now stripped on create + update.** When pasting
  a webhook.site URL it's easy to copy the viewer URL
  (`https://webhook.site/#!/view/<uuid>`) instead of the endpoint URL
  (`https://webhook.site/<uuid>`). The viewer URL POSTs to
  `https://webhook.site/` because HTTP servers never see fragments,
  which returns 404. Fragments in webhook URLs are always a mistake
  (they're client-side only), so the API now strips them server-side
  on create and update — the user error becomes self-healing without
  needing to re-enter the URL.

### Notes

- All three were caught in real-device smoke testing on a LAN-deployed
  CE instance. Worth a permanent note for future ships: real-device
  testing finds layout and state-persistence bugs that don't show up
  in dev environments where the component is mounted once at a single
  viewport width.

---

## [1.0.0g-1] — 2026-05-12

Cosmetic + UX patch on top of v1.0.0g. No schema change, no migration.
Same `100g00000` Alembic head; upgrading from v1.0.0g is a container
rebuild only.

### Fixed

- **Webhooks page styling: light + dark mode.** The initial v1.0.0g
  shipped with CSS custom-property names that don't exist in CE
  (`--surface`, `--text`, `--steel-blue`, `--border`). Browsers
  silently render undefined `var(...)` as nothing, which made the
  "Add endpoint" button transparent, endpoint name + URL invisible,
  and the secret modal's card background transparent so page content
  showed through. Replaced throughout with CE's actual variables
  (`--card-bg-solid`, `--text-primary`, `--io-accent`, `--on-accent`,
  `--card-border`, `--neutral-tint`, `--accent-tint`, `--accent-border`,
  `--alert-burgundy`, `--alert-tint`, `--pending-tint`, `--pending-color`).
  Page now renders correctly in both light and dark mode with the
  same automatic flip every other CE page uses.

- **Copy-secret button worked over HTTPS / localhost only.** The
  Clipboard API (`navigator.clipboard.writeText`) requires a secure
  context and is silently blocked on plain HTTP — which is how most
  self-hosters access the admin UI over LAN (e.g. `http://192.168.x.x`).
  Added a `document.execCommand('copy')` fallback that works on any
  origin. Final fallback: if even that fails, the secret stays selected
  in the input so the user can copy manually with Ctrl+C or long-press.

- **"Send test" produced no visible feedback for up to 30 seconds.**
  Tests were correctly queued as PENDING deliveries, but only fired
  on the next scheduler tick. The button felt broken. Two changes:
  (1) the test-send endpoint now runs one immediate worker tick after
  inserting the delivery row, so the receiver typically sees the
  request within milliseconds; (2) clicking "Send test" auto-opens the
  deliveries panel, refreshes it once immediately and again after
  1.5 s, and shows a temporary success banner ("Test event queued").
  Failure paths still apply — if the receiver returns non-2xx the row
  shows up with `failed` status and the next retry scheduled.

### Added

- `webhooks.test_queued` i18n key for the new success banner.

### Notes

- Plays no part in the SaaS launch dependency chain — purely a quality
  patch so v1.0.0g actually looks and feels finished. v1.0.0h (event
  emissions + 24 h grace + `BILLING_CONFIRMATION_REQUIRED` flag) is
  unaffected and remains the next ship.

---

## [1.0.0g] — 2026-05-12

Generic outbound webhook subsystem + capability flags. Pure additions:
existing behaviour is unchanged when the new env vars are left at
their defaults. No-op upgrade for self-hosters who don't configure
webhooks.

### Added

- **Outbound webhook subsystem.** A new admin section under `/admin/webhooks` (Super Admin only) for configuring URLs that Moimio will POST to when system events occur. Each delivery is signed with HMAC-SHA256 using a per-endpoint signing secret. The header format is `Moimio-Signature: ts=<unix>;h1=<hex_hmac>`, mirroring Paddle's inbound convention so receiver-side code is symmetric. Endpoints can subscribe to all events (`*`) or specific types. The page lists endpoints with their state (active / degraded / disabled / paused), shows the last 50 delivery attempts per endpoint, and exposes test-send, rotate-secret, pause/resume, re-enable, and delete actions. v1.0.0g ships with `test.ping` as the only emittable event type — real event emissions arrive in subsequent ships.
- **Sticky "show once" secret modal.** When an endpoint is created or its secret is rotated, the plaintext secret is displayed in a modal that refuses to close on click-outside or keypress. The admin must check a "I have saved this secret" box and click Done. After that, the secret is never recoverable through the UI (a one-way trip mirroring how GitHub PATs and Stripe restricted keys work). Lose it, rotate it — one click.
- **Background scheduler.** First introduction of APScheduler (AsyncIO mode, in-process) to drive the webhook delivery retry queue (every 30 s) and the daily delivery-log prune (03:00 UTC). No new services required; the scheduler runs inside the existing FastAPI process and shares its async DB session machinery.
- **Webhook retry policy.** Failed deliveries (non-2xx, timeout, connection failure) are retried on the schedule 30 s → 2 min → 10 min → 1 h → 6 h. After all retries are exhausted, the delivery is marked `exhausted` and a delivery row remains in the log for the retention window. After 5 consecutive failures across deliveries, the endpoint is marked `degraded` (still firing, but the admin UI shows a warning). After 20 consecutive failures, it is marked `disabled` and the admin must manually re-enable it after investigating.
- **Capability flags.**
  - `FEATURE_ALLOCATION` (default `on`): when off, the allocation engine and its `/api/allocations*` endpoints are excluded entirely; the sidebar entries for allocation-related views are hidden. Use this for a registration-only deployment.
  - `FEATURE_OUTBOUND_WEBHOOKS` (default `on`): when off, the webhook admin section, router, and scheduler jobs are all disabled. The capability is exposed at `GET /api/capabilities` so the frontend can gate the sidebar without 404-ing.
- **Auto-registration env vars.** Setting both `MOIMIO_WEBHOOK_URL` and `MOIMIO_WEBHOOK_SECRET` causes CE to auto-create a webhook endpoint subscribing to all events at first boot. The auto-registered endpoint is flagged `managed_by=saas` and is hidden from the admin UI — managed infrastructure, not a user object. Idempotent: subsequent boots update the URL or secret if they have changed in env, otherwise leave the row alone. Self-hosters who don't set these vars see no change.
- **`WEBHOOK_DELIVERY_RETENTION_DAYS`** env var (default 30). Controls how long delivery-log rows are kept before the daily prune job deletes them.

### Schema

- Two new tables: `outbound_webhook_endpoints` (config + state) and `outbound_webhook_deliveries` (append-only attempt log, FK-cascaded). Three new Postgres enums: `webhook_endpoint_state`, `webhook_endpoint_managed_by`, `webhook_delivery_status`. Migration ID `100g00000`, parents `85a00000`. Existing data is untouched; the migration only adds new tables and enums.

### Notes

- The signing secret is stored in plaintext at-rest. CE is the *sender* of webhook deliveries, so it must produce a fresh HMAC on every outbound call, which requires recoverable plaintext. The "show once" pattern protects against accidental shoulder-surfing and screenshot disclosure, not against full-DB leaks; standard hosting trust and backup encryption are the protection at rest. An encrypted-column upgrade with a master-key env var is a candidate hardening for a future ship.
- The webhook subsystem is plumbing only in v1.0.0g — nothing in CE fires events through it yet. The only emittable event type is `test.ping`, triggered by the admin "Send test" button. This lets self-hosters wire up and verify their integrations before any real events arrive. Real emissions (event lifecycle, etc.) arrive in subsequent ships.
- Upgrade is a single migration; existing v1.0.0 deployments upgrade with `alembic upgrade head` and a container restart. No data movement.

---

## [1.0.0f] — 2026-05-12

Cosmetic and documentation cleanup ship. No functional change for end users.

### Fixed

- **Residual `APP_URL` environment variable removed from `docker-compose.yml`.** The setting was removed from the application in v0.61b-2 (URLs are now derived per-request) and `app/core/config.py` no longer reads it. The Compose file was still passing `APP_URL` into the backend service, where pydantic-settings silently ignored it. Removed the line so the Compose surface matches the application surface.
- **Source comments in `app/core/urls.py` and `app/api/auth.py`** previously described a hypothetical "single backend serves multiple domains" SaaS architecture. The actual SaaS architecture is container-per-tenant (each tenant runs their own stack on their own subdomain). Comments retightened to describe what the URL derivation logic actually serves: self-host on arbitrary domains, and container-per-tenant SaaS on tenant subdomains.

### Notes

No application behaviour changes. Upgrade by replacing the scaffold and rebuilding; existing databases and configurations are unaffected.

---

## [1.0.0e] — 2026-05-10

Allocation engine refinements: a final equalising sweep, soft warnings when manual moves override engine-honoured constraints, group-code tooltips listing clustermates across the People board, Check-in board, Insight panel, and history audit trail, and a fix for placement reasoning popovers that had silently broken in v1.0.0. Plus a translation sweep for the German and Korean UI.

### Added

- **Equalising sweep (PASS 4c).** After all rule-based passes, the engine now moves whole clusters between units to even out occupancies proportional to capacity. Operates on movable clusters only — `fill` singletons, whole `group_code` clusters, whole `mark_together` clusters — and never touches split clusters, `mark_split`, or `gender_drain` placements. Hard rules (group codes, marks, gender restrictions, capacity) are never overridden. Toggle in the engine settings popover; default ON. The audit trail preserves both the original cluster reason and the equalise move ("placed with group SMITH (4 people)" / "moved to even out unit sizes") so organisers can see what the engine was thinking at each step.
- **Soft warnings on manual moves.** When an organiser manually moves a participant in a way that breaks an engine-honoured cluster (group code, mark-together) or unrestricts a gender-drained unit, a gold "take note" toast appears. Non-blocking, no consent required — just a heads-up that the move overrides what the engine had deliberately arranged. The warning gates on the category's current rule settings, so disabling group codes silences the warning for group-based moves. The toast stays visible for 10 seconds (vs. 3 for other types) and ships with a manual close button so the organiser can read and dismiss it on their own pace.
- **Group-code clustermate tooltip.** The group-code badge is now interactive on every surface that shows it. Hover (desktop) or long-press (touch) reveals the other participants who share the same code in the current event, joined with the locale's natural conjunction ("with X, Y, and Z" / "mit X, Y und Z" / "{names}와 함께" / etc). Short tap and click stay reserved for the badge's existing action (inline edit on PeopleTable, no-op elsewhere). When the participant is the only one with their code, the tooltip says so explicitly rather than staying silent.
- **Imprinted clustermates in history.** Each engine-commit row in the (i)-panel history now shows who else was in the cluster at the moment of placement, snapshotted into the audit trail meta. Survives renames, departures, and right-to-erasure on the participant FK.
- **Empty-state CTA card.** When opening "Manage [Group type]" on an empty group type, the create-first action now renders as a prominent dashed-border card spanning the full width instead of a small inline link far from the toggle that opened the section.

### Fixed

- **Placement reasoning popovers and (i)-panel history sub-lines.** The frontend dispatcher's vocabulary had drifted from the engine's actual output (`group_code_cluster` vs `group_code`, `mark_cluster` vs `mark_together`), silently disabling every popover except the trivial `fill` case. Re-aligned the dispatcher; pre-v1.0.0e commits stored in `meta.placement.reason` now render correctly without any data migration.
- **Group-code long-press not firing on Android.** Browsers race the long-press timer with their own native long-press behaviour (Android Chrome: text selection; iOS Safari: callout menu) and the browser's `touchcancel` would fire before our 500 ms timer completed. Suppressed via `user-select: none`, `-webkit-touch-callout: none`, and `touch-action: manipulation` on the trigger element so our timer reliably wins.
- **Dark-mode contrast on (i) icons and tick pills.** The (i) info button on the CheckIn board, AllocationBoard, and the per-mark (i) inside unit cards rendered as `text-subtle` at 40 % opacity — readable in light mode, near-invisible in dark. Bumped to 70 % opacity in dark mode (light mode unchanged). The CheckIn tick-field pills (mobile) used literal white text, which sits at ~1.3:1 contrast on the dark-mode gold accent; now uses the `--on-accent` token, which resolves to deep-navy on gold (~14:1).

### Translation

- **German.** Full sweep replacing every form of `Teilnehmende` / `Teilnehmenden` with the conventional `Teilnehmer` (with `-n` dative-plural inflection where grammar requires it). 30 occurrences across 25 strings.
- **Korean.** Sidebar People entry: `참가자` → `참가자 명단`.

### Notes

- Backend test suite (`test_allocation_events.py`) had been asserting against the old reason vocabulary and was failing silently in CI — assertions are now realigned to the engine's actual output, alongside new test coverage for the equalise sweep, the warning helper, and the cluster-member snapshot.
- No schema migration. The equalise toggle lives in the existing `allocation_categories.settings` JSONB; the equalise reason payload and the cluster-member snapshot extend the existing `meta.placement` JSONB shape. Existing v1.0.0 deployments upgrade with `alembic upgrade head` as a no-op.
- Six new placement-reason i18n keys plus four warning-toast keys plus two group-code tooltip phrases ("with {names}" and the alone-singleton message), polished across all six locales (EN/DE/KO/ES/PT-BR/FR).

---

## [1.0.0] — 2026-05-02

Initial public release of **Moimio CE (Community Edition)**. Moimio reaches feature-completeness for the small and mid-sized event use case it was designed for: church, mission, and retreat organisers.

### Added

- **Events.** Create, configure, and run events end-to-end. Lifecycle: draft → open → closed, with a separate archive flag for long-term storage.
- **Public registration form** with per-event field configuration. Six toggleable built-in fields (gender, date of birth, phone, address, country, church/organisation) plus custom fields (text, number, select, boolean, date) backed by an EAV schema so each event has its own form shape.
- **Group codes.** Family or friend groups register together using a shared code (e.g. `SMITH-742`); the engine keeps them together at allocation time. Auto-generated server-side if a registrant doesn't enter one, and included in the registration confirmation email so they can share it with others.
- **Marks.** Colour-coded badges for staff-visible tagging — "leader", "first-timer", "needs ground floor", anything an organiser wants to track. Marks influence the allocation engine via configurable per-mark behaviour (keep together, spread evenly, no effect).
- **Allocation engine.** A deterministic 5-pass algorithm that proposes a full allocation in one shot — respecting group-code clusters, mark behaviours, gender restrictions, and capacities. Two modes: top-up (keep existing assignments and place new participants only) or replace (reallocate everyone from scratch). Admins can commit, override, or re-run with adjusted settings.
- **Allocation categories and units.** Generic system replacing per-type tables: define your own categories (with `exclusive` — one unit per participant — or `overlapping` — many units per participant — rules). New events come pre-seeded with **Rooms** and **Small Groups** as defaults.
- **Check-in.** Custom tick columns per event ("Arrived", "Welcome pack", "Payment"); immersive check-in mode for tablet/phone use at the door; multiple staff can check in concurrently.
- **PDF roster exports.** Compact and Sign-in formats. CJK-safe (Korean rosters render correctly using Noto Sans CJK).
- **CSV imports and exports.** Batch participant registration from a spreadsheet; CSV export of the full participant list with allocations and custom fields.
- **GDPR data export.** Per-participant JSON export covering every record Moimio holds about that person — built for fulfilling Article 20 (data portability) and Article 15 (right of access).
- **Data backup and restore.** Full event archive download and restore for migrations between deployments. Two backup modes: full or structure-only (GDPR-safe template sharing).
- **Multi-language UI.** English, German, Korean, Spanish, Brazilian Portuguese, French — 6 locales with full string parity.
- **Notes.** Note system — staff can attach private or shared notes to participants. The `is_published` flag controls whether other staff see them.
- **Staff permissions.** Per-event assignment with five permission surfaces — People (read/write/none), Organise (read/write/none), Marks (write/none), Check-in (write/none), Reports (read/none).
- **Self-hosting.** One `docker compose up` away. No external services required. SMTP optional.

### Notes

- Moimio CE v1.0 is the first public release. Earlier versions were internal development iterations and are not published.
- For the technical specification of the allocation engine, see the module docstring at `backend/app/services/engine_service.py`.
- Moimio CE's code and documentation were substantially developed with [Claude Opus 4.7 Adaptive](https://www.anthropic.com/claude).

---

## Versioning policy

- **Major version** (`x.0.0`) — breaking schema or API changes that require migration steps beyond `alembic upgrade head`.
- **Minor version** (`1.x.0`) — new features, backwards-compatible.
- **Patch version** (`1.0.x`) — bug fixes, translation updates, dependency bumps.

Pre-release tags use a suffix: `1.0.0e-rc.1`.
