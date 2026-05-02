"""v50b schema snapshot — use `from app._alembic_snapshots.v50b import Base`
then `Base.metadata` to access the frozen v50b schema definition.

Importing this package triggers all v50b model registrations against
`Base.metadata` (which is isolated from `app.core.database.Base.metadata`).
"""

from ._base import Base  # noqa: F401
from . import models  # noqa: F401  — triggers model registration side-effect
