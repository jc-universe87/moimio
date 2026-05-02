"""Application-level errors with translatable i18n keys.

Introduced v0.70d-3c-2 (M5 finish-up — allocation surface).

Service layer raises `MoimioAppError(key, params, status_code)` instead of
generic `ValueError(str)`. The API layer catches and converts to
`HTTPException(detail={"key": ..., "params": ...})`. The frontend's
`formatErrorMessage(err, t)` then renders the translated key with
parameter substitution.

Single shared class — kept tiny. No per-domain subclasses unless a
real catch-by-type need surfaces. None has so far.
"""


class MoimioAppError(Exception):
    """Application error carrying a translatable key + render parameters.

    Attributes:
        key: i18n key from the `errors.*` namespace (e.g.
            `errors.allocation.unit_gender_restricted`).
        params: dict of substitution values for {placeholder} patterns
            in the translated string. Empty dict if not provided.
        status_code: HTTP status the API layer should map this to. The
            catch site is free to override (e.g. wrap a 404 inside a
            higher-level 409 boundary), but most call sites accept the
            default.
    """

    def __init__(
        self,
        key: str,
        params: dict | None = None,
        status_code: int = 400,
    ):
        self.key = key
        self.params = params or {}
        self.status_code = status_code
        super().__init__(key)

    def to_detail(self) -> dict:
        """Render the detail dict for `HTTPException(detail=...)`.

        Omits `params` entirely when empty so the wire shape stays
        minimal — matches the v0.70d-3b convention used in
        auth/participants/events.py.
        """
        if self.params:
            return {"key": self.key, "params": self.params}
        return {"key": self.key}
