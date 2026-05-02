"""Frozen model snapshots for Alembic baselines.

Each subpackage here (e.g. `v50b/`) is a versioned copy of the ORM
models as they existed at that point in Moimio's history. Each
snapshot uses its OWN `Base` (distinct from `app.core.database.Base`)
so its metadata does not merge with the current models'. This lets
Alembic baseline migrations call `create_all()` against a specific
historical schema rather than whatever the current codebase happens
to define.

Why this pattern exists: prior to v0.52 the baseline migration used
`Base.metadata.create_all()` via the current `app.models` package,
meaning it reflected the latest model state, not the snapshot it was
supposed to represent. Subsequent additive migrations then collided
with columns that were already present in the baseline.

Rule of thumb: these files should be treated as frozen history. Do
not edit a snapshot once it is shipped; create a new snapshot if the
baseline needs to move forward.
"""
