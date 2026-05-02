FROM python:3.12-slim

WORKDIR /app

# Brand font (Nunito) is self-hosted at app/fonts/Nunito-*.ttf,
# mirroring the frontend's /public/fonts/ pattern. fonts-noto-cjk
# stays apt-sourced because it's ~92 MB and not part of brand
# identity — only used as a glyph fallback for Korean/Chinese/
# Japanese names in PDF roster exports.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev fonts-noto-cjk && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# PYTHONPATH so Alembic (run from /app/alembic/) can find app.core.config.
# Without this, `alembic upgrade head` fails with ModuleNotFoundError.
ENV PYTHONPATH=/app

EXPOSE 8000

# On container start:
#   1. Wait briefly for the DB to accept connections (simple sleep — works
#      for dev/prod alike; compose's depends_on ensures the db container
#      is up but not that Postgres is ready to accept queries).
#   2. Run any pending Alembic migrations. Idempotent — does nothing if
#      already at head.
#   3. Launch uvicorn.
#
# The one-liner is in shell form so the && chain short-circuits on failure
# — if migrations fail, uvicorn doesn't start, and compose will report the
# container as unhealthy.
CMD sh -c "sleep 3 && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
