"""The one place the backend's version is written (v1.0.4d).

`app/main.py` (startup log and API metadata) and `/health` read it from
here. The frontend keeps its own marker in `frontend/package.json`
(`moimioVersion`, with a leading "v"); `scripts/check-version-markers.py`
fails the CI `checks` job if the two disagree, and on a tag push, if the
tag or the CHANGELOG heading disagree with them. Bump both with
`scripts/bump-version.py <version>`.
"""

__version__ = "1.0.4d"
