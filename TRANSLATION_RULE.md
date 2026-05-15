# Translation Rule

> **After every frontend UI change, the translation files must be updated.**

## Location

```
frontend/src/i18n/locales/en.json
frontend/src/i18n/locales/de.json
frontend/src/i18n/locales/ko.json
frontend/src/i18n/locales/es.json
frontend/src/i18n/locales/pt-BR.json
frontend/src/i18n/locales/fr.json
```

> **Loading model:** English is statically imported as the `t()` fallback
> dictionary, ensuring every key always resolves. The other 5 locales are
> dynamically imported per user when they switch language. See
> `frontend/src/hooks/useI18n.jsx` for the loader logic.

## Languages (all 6 must be updated)

| Code     | Language              | File                  |
|----------|-----------------------|-----------------------|
| `en`     | English               | `locales/en.json`     |
| `de`     | German                | `locales/de.json`     |
| `ko`     | Korean                | `locales/ko.json`     |
| `es`     | Spanish               | `locales/es.json`     |
| `pt-BR`  | Brazilian Portuguese  | `locales/pt-BR.json`  |
| `fr`     | French                | `locales/fr.json`     |

Lowercase `pt-BR` (exact case) is the canonical code — it must match
`SUPPORTED_LANGS` in `useI18n.jsx`.

## Per-locale conventions (address forms and terminology)

These are language-specific defaults that must be kept consistent across
every string. Drift here makes the UI feel translated rather than
written — same problem as inconsistent terminology in EN.

### Address form (who is the user being addressed as)

| Locale  | Form     | Notes                                                |
|---------|----------|------------------------------------------------------|
| `en`    | you      | Neutral; no T/V distinction.                          |
| `de`    | **du**   | Always informal. Never `Sie` for direct address.     |
| `ko`    | 합니다체 / -세요 (formal-polite) | Standard polite-formal endings for instructions. |
| `es`    | **tú**   | Always informal. Never `usted` for direct address.   |
| `pt-BR` | você     | Standard pt-BR neutral form.                         |
| `fr`    | **vous** | Always formal. Never `tu` for direct address.        |

**DE, ES, and FR are the three with hard rules: DE is always du, ES is
always tú, FR is always vous.** These were product decisions, not
translator choices, and they must not drift.

In DE, `Sie` may legitimately appear as the 3rd-person pronoun referring
to a noun (`die Spalten ... sie werden`, `diese Person ... sie wird`) —
that is not address-form drift. The same is true in ES for the verb
`puede` referring to a 3rd-party noun (`el personal puede ver...`) or
in impersonal constructions (`no se puede deshacer`). Only the
**direct-address** use of `Sie` / `usted` is drift.

### Terminology notes

- **DE**: "Event" (loan-word) is the canonical term for a Moimio event,
  not "Veranstaltung". For the 24h grace cancel action the verb is
  **"absagen"** (call off) — chosen over "stornieren" (commercial
  reversal) because the admin's mental model is calendar-cancellation
  rather than transaction-reversal.
- **Brand and protocol names** (Moimio, Slack, Zapier, Paddle,
  HMAC-SHA256, Moimio-Signature, URL, POST) are kept as-is in every
  locale.
- **Quotation marks** should be locale-native where the locale has a
  preference: DE „…", FR «\u00a0…\u00a0», KO/ES/pt-BR "…".

## How to Add a New String

1. Choose a key following the naming convention: `namespace.sub.descriptor`
2. Add it to `locales/en.json` first
3. Add translations for all 5 other locale files
4. Use it in the component: `{t('your.new.key')}`
5. Keep keys alphabetically sorted within each file
6. Run `npm run validate-i18n` to confirm the validator passes (it
   will also fire automatically as a pre-Vite step on `npm run build`)

**Never ship hardcoded text in JSX.**

If a key is present in `en.json` but missing from another locale file,
the `t()` function silently falls back to the English string at runtime.
This is a safety net, not a feature — parity is the contract.

## Key Naming Convention

```
common.*          shared primitives (save, cancel, delete, close, loading…)
status.*          event/participant statuses (used dynamically: t('status.' + x))
role.*            user roles (used dynamically: t('role.' + x))
nav.*             sidebar navigation
events.*          events list page
event.*           event detail/setup sections
register.*        public registration form
organise.*        allocation board and dashboard
engine.*          allocation engine UI
engine.settings.* per-category engine settings
alloc.*           allocation moments (ready/confirmed banners, next-category hint)
checkin.*         check-in panel
marks.*           colour badge system
staff.*           staff roles and assignments
users.*           user management
notes.*           notes system
prefs.*           user preferences
grouping.*        group preference form (registration-side)
style.*           style customiser
confirm.*         email confirmation page (state machine: fresh/already/invalid/network)
install.*         PWA install prompt
update.*          PWA update prompt
insight.*         InsightPanel
allocations.history.*  allocation event timeline
batch.*           batch registration (Phase 2.6)
portability.*     data export/restore (Phase 2.7)
export.pdf.*      PDF roster export (Phase 2.5)
welcome.*         welcome panel + phase story sections
errors.*          backend error keys (see "Backend errors" below)
```

## Backend errors — dict-detail convention

The backend signals user-facing errors to the frontend by raising
`HTTPException` with a structured detail dict instead of an English
string. Three files use this convention so far:

```python
# backend/app/api/auth.py, participants.py, events.py
raise HTTPException(
    status_code=400,
    detail={"key": "errors.event.cannot_create_no_name"}
)

# Or with parameters:
raise HTTPException(
    status_code=409,
    detail={"key": "errors.participant.email_in_use", "params": {"email": email}}
)
```

The frontend's `services/api.js::request()` extracts the key and
exposes it as `err.i18nKey`. Components render via the
`formatErrorMessage(err, t)` helper from the same file, which
returns `{primary, detail}` for Pattern B rendering (friendly
translated string as primary line, raw backend message as muted
secondary detail, or `null` for network failures).

Other backend files still raise string-detail. The frontend
categories layer handles those gracefully via `friendlyKey`
(based on HTTP status), so coverage can be extended incrementally.
The remaining ~70 raise sites (allocation, marks, customFields,
notes) are on the backlog.

The 1 exception in `participants.py` (`detail={"state": "invalid"}`
for ConfirmPage's three-state machine) is structured detail
consumed by frontend logic, not an error message — kept as-is.

## Validation

Run this to check for missing or extra keys across the 6 locale files:

```bash
cd frontend && npm run validate-i18n
```

The script (`frontend/scripts/validate-i18n-keys.py`) is wired into
`npm run build` as a pre-Vite step, so missing keys fail the Docker
build before deploy. The validator scans every static `t('key')`
callsite in `src/` and confirms it resolves against `locales/en.json`.
Template-literal forms (`t(\`x.${y}\`)`) and variable-key forms
(`t(labelKey)`) are reported as informational rather than failures.

## Operator workflow — translation overhaul drop-ins

Two scripts in `frontend/scripts/` handle the round-trip with an
external translation pipeline:

**Splitter** — convert a unified file (a single JSON object with
one block per language at the top level) into the per-locale files:

```bash
cd frontend
python3 scripts/split-translations.py /path/to/your/unified.json
# → writes src/i18n/locales/{en,de,ko,es,pt-BR,fr}.json
```

The splitter preserves alphabetical key order, validates that all 6
languages are present in the input, and refuses to overwrite if the
input is missing keys that exist in the current locale files (defensive
against accidental drops of stale data).

**Exporter** — inverse direction, assembles the 6 per-locale files
into a unified JSON for sending to a translation service:

```bash
cd frontend
python3 scripts/export-translations.py /path/to/output/unified.json
# → reads src/i18n/locales/*.json, writes the unified file
```

Parity-validated, round-trip-safe with the splitter — running
exporter then splitter on a clean tree is a no-op.

## Current Status

**1,041 keys × 6 languages = 6,246 translations.** All aligned. Zero
missing. Validator clean.
