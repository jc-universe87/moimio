"""Isolated DeclarativeBase for the v50b model snapshot.

Kept separate from `app.core.database.Base` so the two registries
don't merge. This base owns only the v50b tables; `create_all()`
against its metadata produces exactly the v50b schema.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Isolated declarative base for the v50b snapshot only."""
    pass
