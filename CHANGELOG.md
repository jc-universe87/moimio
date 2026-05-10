# Changelog

All notable changes to Moimio CE are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0e/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This is the public, user-facing changelog. Detailed per-development-iteration history is kept internally and is not published.

---

## [Unreleased]

Nothing yet. Open issues at <https://github.com/jc-universe87/moimio/issues> for things you'd like to see.

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
