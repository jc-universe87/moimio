# Contributing to Moimio CE

Thanks for your interest in contributing. Moimio CE is a small project with a clear scope, so a few words about the spirit of contribution before the mechanics.

## Project philosophy

A fuller architectural reference is at [`ARCHITECTURE.md`](ARCHITECTURE.md) — read it before designing any non-trivial change. The short version:

Moimio CE is built for **small and mid-sized event organisers** — churches, missions, retreats. Decisions about features, scope, and architecture are filtered through that lens. A request that makes Moimio more enterprise-flexible at the cost of being harder to set up for a volunteer organiser is, almost always, the wrong direction.

We also care about:

- **Self-hostability.** Anything that introduces a hard dependency on a third-party service (analytics, hosted databases, paid APIs) should be optional, configurable, or rejected.
- **GDPR-first.** Personal data stays inside the deployment. New features must respect that.
- **Doing the obvious thing well.** Moimio prefers a smaller feature that's reliable over a larger feature that's clever.

If you have a feature idea that pushes against any of these, please open an issue to discuss before writing code. A short written exchange (or, where it makes sense, a brief call) usually clarifies the right direction faster than a rejected PR.

## A note on this project's development

Moimio CE's code and documentation were substantially developed with [Claude Opus 4.7 Adaptive](https://www.anthropic.com/claude). This is mentioned not for credit but for transparency: if you ask the maintainer a deeply technical question — about, say, the precise behaviour of an internal helper, the exact rationale for a v0.4x design choice, or a subtle interaction between services — the maintainer's answer may be "let me run it past Claude," which is the same workflow that produced the code in the first place. We mention this so you know what to expect.

---

## Reporting bugs

Open a [bug report](https://github.com/jc-universe87/moimio/issues/new?template=bug_report.md). The template asks for the information we need: what happened, what you expected, how to reproduce, and the versions involved.

If you found a **security issue**, please do *not* open a public issue. Use [GitHub's private vulnerability reporting](https://github.com/jc-universe87/moimio/security/advisories/new) — see [SECURITY.md](SECURITY.md).

## Suggesting features

Open a [feature request](https://github.com/jc-universe87/moimio/issues/new?template=feature_request.md). Describe the problem first, then your proposed solution. Tell us which kind of organiser this helps — the more concrete the use case, the easier it is to scope the work.

## Sending pull requests

**Open an issue first.** Even a one-line issue is fine — it lets us flag scope concerns before you've written code, and it gives the PR a tracked context.

Mechanically:

1. Fork the repo.
2. Create a branch from `main`. Suggested naming: `feat/short-description`, `fix/short-description`, `docs/short-description`.
3. Make your changes. Keep PRs focused — one concern per PR.
4. Test locally (see "Development setup" below).
5. Open a PR against `main`. The PR template asks for a description, linked issue, and a checklist.

We'll review as time allows. Moimio CE is maintained by one person in spare time, so reviews may take a few weeks. Please don't take a delay as disinterest — it's a queue, not a verdict.

---

## Development setup

The fastest way to get a working dev environment:

```bash
git clone https://github.com/jc-universe87/moimio.git
cd moimio
cp .env.example .env
docker compose up -d --build
```

Frontend at `http://localhost:6120`, backend at `http://localhost:6121`, API docs at `http://localhost:6121/docs`.

For non-Docker setups (running backend and frontend natively for faster iteration), see the comments in `backend/Dockerfile` and `frontend/Dockerfile` — both are reproducible by hand if you have Python 3.12, Node 20+, and PostgreSQL 16 locally.

### Running tests

```bash
docker compose exec backend pytest
```

### Linting the frontend

```bash
docker compose exec frontend npm run lint
```

ESLint v9 with a flat config. Some `react-hooks/exhaustive-deps` warnings are accepted backlog — please don't add new ones in your PR.

---

## Architecture notes

The product- and architecture-level *why* is in [`ARCHITECTURE.md`](ARCHITECTURE.md). Beyond that, the architecture lives in the source code, with module-level docstrings doing the heavy lifting. Good places to start:

| Topic | Where to look |
|---|---|
| Product invariants and design principles | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| Allocation engine algorithm | `backend/app/services/engine_service.py` (top-of-file docstring) |
| Database schema | [`docs/data-model.md`](docs/data-model.md) |
| GDPR architecture | [`docs/gdpr-compliance.md`](docs/gdpr-compliance.md) |
| Translation system | [`TRANSLATION_RULE.md`](TRANSLATION_RULE.md) |
| API surface | `http://localhost:6121/docs` (auto-generated OpenAPI) |
| Backend entry point | `backend/app/main.py` |
| Frontend entry point | `frontend/src/main.jsx` |

---

## Translation contributions

Adding or improving a translation is one of the most useful contributions you can make.

- The full translation system is documented in [TRANSLATION_RULE.md](TRANSLATION_RULE.md).
- Locale files live at `frontend/src/i18n/locales/{en,de,ko,es,pt-BR,fr}.json`.
- Run `npm run validate-i18n` (inside the frontend container) before submitting — it checks key parity across the 6 locales.
- If your PR adds new UI strings, add the key to **all 6** locale files in the same PR. English is the source of truth; missing keys in other locales fall back to English at runtime, but parity is the contract.

To **add a new language**: open an issue first so we can confirm the locale code (BCP 47) and add it to `SUPPORTED_LANGS` in `frontend/src/hooks/useI18n.jsx`.

---

## Style and conventions

- **Backend:** Standard Python style. We use SQLAlchemy 2.x async patterns; please keep new code in that style. New API routes go in `backend/app/api/`, new services in `backend/app/services/`.
- **Frontend:** Functional React with hooks. Tailwind utility classes for styling; avoid introducing new CSS files. Keep components in `frontend/src/components/` (shared) or co-located with their parent page.
- **Commits:** Clear, sentence-style commit messages. Reference the issue (`#123`) where relevant.
- **No hardcoded strings in JSX.** Use `t('your.key')`. See [TRANSLATION_RULE.md](TRANSLATION_RULE.md).
- **Schema changes** require an Alembic migration. Generate with `alembic revision --autogenerate`, then review and edit the generated file before committing.

---

## Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). Conduct concerns: `contact@moimio.app`.

---

## Licence

By contributing to Moimio CE, you agree that your contributions will be licensed under the [MIT Licence](LICENSE).
