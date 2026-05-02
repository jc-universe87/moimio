<!-- Thanks for sending a PR. A few quick checks before submitting:

     - Open an issue first if you haven't (even a one-line one).
     - One concern per PR. Smaller is easier to review.
     - Run the test suite and the i18n validator (where applicable) locally. -->

## Summary

<!-- One or two sentences: what does this PR do, and why? -->

## Linked issue

<!-- Closes #issue_number     OR     Refs #issue_number     OR     N/A -->

## Type of change

<!-- Tick what applies. -->

- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change (requires migration steps beyond `alembic upgrade head`)
- [ ] Documentation only
- [ ] Translation only
- [ ] Internal refactor / cleanup (no behavioural change)

## Checklist

- [ ] My PR is focused on a single concern.
- [ ] I've tested the change locally (`docker compose up -d --build` and exercised the affected workflow).
- [ ] I've added or updated tests where it made sense to.
- [ ] **If the PR adds or changes UI strings:** I've added the new keys to all 6 locale files (`en`, `de`, `ko`, `es`, `pt-BR`, `fr`) and `npm run validate-i18n` passes.
- [ ] **If the PR changes the database schema:** I've generated an Alembic migration and reviewed it (`backend/alembic/versions/`).
- [ ] **If the PR touches the allocation engine:** I've considered impact on the documented hard constraints (gender restriction, capacity) and the soft-constraint priority order.
- [ ] I've updated relevant documentation (`docs/`, `README.md`, `CHANGELOG.md`) where the change is user-facing.

## Screenshots

<!-- For UI changes, before/after screenshots help a lot. -->

## Notes for the reviewer

<!-- Anything else you'd like the reviewer to know — design decisions you
     made, alternatives you considered, things you're unsure about. -->
