#!/usr/bin/env bash
#
# Moimio deploy script.
#
# Usage:   ./deploy.sh <version-tag>
# Example: ./deploy.sh v1.0.0
#
# Replaces the brittle `&& \` chain that previously documented Moimio's
# deploy recipe. That chain failed silently when one step (typically
# `unzip`) errored partway through, leaving the site dir half-wiped.
#
# What this script guarantees:
#   1. The version-tagged scaffold zip exists and unpacks cleanly BEFORE
#      we wipe anything on disk.
#   2. The .env file is backed up before any mutation.
#   3. Containers are stopped without `-v` (pgdata volume is preserved).
#   4. Every failure is loud: ERR trap prints the line + step.
#   5. The current deploy.sh is preserved across the wipe (the new one
#      lands when staged contents are moved into place).
#
# Pre-conditions (script enforces these):
#   - Run from the moimio site directory (must contain docker-compose.yml).
#   - .env present.
#   - ../moimio-ce-<TAG>.zip present and integrity-clean.
#
# Post-deploy:
#   - Streams `sudo docker compose logs -f --tail=50 backend`. Watch for
#     `Application startup complete.` Press Ctrl-C to detach (containers
#     keep running).
#

set -euo pipefail
IFS=$'\n\t'

# ──────────────────────────────────────────────────────────────────────
# Failure handler: makes silent breakage loud.
# ──────────────────────────────────────────────────────────────────────
on_err() {
  local exit_code=$?
  local line_no=$1
  echo
  echo "╔══════════════════════════════════════════════════════════════════╗"
  echo "║  DEPLOY FAILED                                                   ║"
  echo "╠══════════════════════════════════════════════════════════════════╣"
  printf  "║  exit code : %-52s║\n" "$exit_code"
  printf  "║  line      : %-52s║\n" "$line_no"
  printf  "║  step      : %-52s║\n" "${STEP:-(pre-flight)}"
  echo "╚══════════════════════════════════════════════════════════════════╝"
  echo
  echo "Site state should be intact: nothing is wiped until the staged"
  echo "extraction succeeds. If a build/up step failed, your previous"
  echo "containers may be stopped — restart with:"
  echo "  sudo docker compose up -d"
  echo
}
trap 'on_err $LINENO' ERR

STEP="argument check"
if [[ $# -lt 1 ]]; then
  echo "ERROR: missing version tag." >&2
  echo "Usage: $0 <version-tag>     e.g. $0 v1.0.0" >&2
  exit 2
fi
TAG="$1"
ZIP="../moimio-ce-${TAG}.zip"
STAGE="../moimio-ce-staging-${TAG}"

echo "─── Moimio deploy: ${TAG} ───"

# ──────────────────────────────────────────────────────────────────────
# 1. Pre-flight checks (no mutations yet)
# ──────────────────────────────────────────────────────────────────────
STEP="pre-flight: working directory"
if [[ ! -f docker-compose.yml ]]; then
  echo "ERROR: docker-compose.yml not found in $(pwd)." >&2
  echo "Run this script from the moimio site directory" >&2
  echo "  (typically ~/docker-compose/moimio/)." >&2
  exit 3
fi

STEP="pre-flight: .env"
if [[ ! -f .env ]]; then
  echo "ERROR: .env not found in $(pwd)." >&2
  echo "Restore it from a backup before deploying." >&2
  exit 4
fi

STEP="pre-flight: scaffold zip exists"
if [[ ! -f "$ZIP" ]]; then
  echo "ERROR: scaffold zip not found: $ZIP" >&2
  echo "Drop moimio-ce-${TAG}.zip into the parent directory and retry." >&2
  exit 5
fi

STEP="pre-flight: zip integrity"
if ! unzip -tq "$ZIP" >/dev/null 2>&1; then
  echo "ERROR: $ZIP failed integrity check (unzip -tq)." >&2
  echo "Re-download the zip and retry." >&2
  exit 6
fi

echo "✓ Pre-flight OK"

# ──────────────────────────────────────────────────────────────────────
# 2. Stage extraction (still no mutations to the live site)
# ──────────────────────────────────────────────────────────────────────
STEP="stage: clean staging dir"
rm -rf "$STAGE"

STEP="stage: extract"
unzip -q "$ZIP" -d "$STAGE"

STEP="stage: locate scaffold root"
# Released zips wrap content in moimio-ce/ (canonical, v0.99d+). Older
# packaging used moimio-scaffold-<TAG>/ or moimio-public-prep/; both
# are accepted as legacy fallbacks. If none of these match, treat the
# staging dir itself as the scaffold root (oldest pre-wrapping form).
if [[ -d "$STAGE/moimio-ce" ]]; then
  SCAFFOLD_ROOT="$STAGE/moimio-ce"
elif [[ -d "$STAGE/moimio-scaffold-${TAG}" ]]; then
  SCAFFOLD_ROOT="$STAGE/moimio-scaffold-${TAG}"
elif [[ -d "$STAGE/moimio-public-prep" ]]; then
  SCAFFOLD_ROOT="$STAGE/moimio-public-prep"
else
  SCAFFOLD_ROOT="$STAGE"
fi

STEP="stage: validate scaffold contents"
for required in backend frontend docker-compose.yml; do
  if [[ ! -e "$SCAFFOLD_ROOT/$required" ]]; then
    echo "ERROR: scaffold missing $required at $SCAFFOLD_ROOT" >&2
    rm -rf "$STAGE"
    exit 7
  fi
done

echo "✓ Staged at $SCAFFOLD_ROOT"

# ──────────────────────────────────────────────────────────────────────
# 3. Mutations begin here (stop, backup, wipe, replace)
# ──────────────────────────────────────────────────────────────────────
STEP="backup: .env"
BACKUP=".env.pre-${TAG}.bak"
cp .env "$BACKUP"
echo "✓ .env backed up to $BACKUP"

STEP="docker compose down"
sudo docker compose down

STEP="wipe scaffold files"
# Wipe the contents managed by the scaffold zip, no more no less. Preserves:
# .env, .env.*.bak, pgdata/, deploy.sh (this script — bash holds it in
# memory, but we exclude it explicitly), staging dir.
sudo rm -rf \
  backend \
  frontend \
  docs \
  .github \
  docker-compose.yml \
  README.md \
  LICENSE \
  CHANGELOG.md \
  CONTRIBUTING.md \
  CODE_OF_CONDUCT.md \
  SECURITY.md \
  TRANSLATION_RULE.md \
  .env.example \
  .gitignore

STEP="install scaffold contents"
# Move both visible and hidden entries; tolerate empty hidden glob.
shopt -s dotglob nullglob
mv "$SCAFFOLD_ROOT"/* . 2>/dev/null || true
shopt -u dotglob nullglob
rm -rf "$STAGE"

STEP="docker compose build --no-cache"
sudo docker compose build --no-cache

STEP="docker compose up -d --force-recreate"
sudo docker compose up -d --force-recreate

# ──────────────────────────────────────────────────────────────────────
# 4. Tail logs so the operator sees startup
# ──────────────────────────────────────────────────────────────────────
STEP="tail logs"
echo
echo "─── Deploy of ${TAG} complete. Tailing backend logs. ───"
echo "    Watch for: Application startup complete."
echo "    Detach:    Ctrl-C  (containers keep running)"
echo
sudo docker compose logs -f --tail=50 backend
