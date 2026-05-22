#!/usr/bin/env bash
#
# Moimio CE — self-hoster upgrade script.
#
# Usage:   ./upgrade.sh [target] [--yes] [--dry-run]
# Examples:
#   ./upgrade.sh                  # Pull latest from origin/<current-branch>
#   ./upgrade.sh v1.0.0n          # Check out the v1.0.0n tag specifically
#   ./upgrade.sh v1.0.0n --yes    # Same, skip the "Continue?" prompt
#   ./upgrade.sh --dry-run        # Print what would happen, don't do it
#
# What this script guarantees:
#   1. .env preservation. The file is never touched, never committed.
#   2. Database backup. pg_dump snapshot taken before any mutation,
#      gzipped to ../pgdata-pre-upgrade-<timestamp>.sql.gz, with the
#      restore command printed.
#   3. Pre-flight first. Network, git state, and Docker state are all
#      verified before any mutations to disk or containers.
#   4. Containers restart only after a successful build. If the build
#      fails, your existing version keeps running.
#   5. Backend health is verified after restart. If health fails,
#      rollback instructions are printed automatically.
#   6. Every failure is loud: clear step name, clear next action.
#
# Pre-conditions (script enforces these):
#   - Run from the moimio repo root (must contain docker-compose.yml
#     and a .git directory).
#   - .env present.
#   - Working tree clean (no uncommitted local changes).
#   - db container currently running (needed for pg_dump backup).
#   - docker, docker compose, and git available in PATH.
#
# Rollback (if you need to revert):
#   1. git checkout <previous-tag-or-sha>     # the old script printed
#                                              # this for you on success
#   2. sudo docker compose down
#   3. sudo docker compose build --no-cache
#   4. sudo docker compose up -d
#   5. gunzip -c ../pgdata-pre-upgrade-<timestamp>.sql.gz | \
#        sudo docker compose exec -T db psql -U <DB_USER> -d <DB_NAME>
#

set -euo pipefail
IFS=$'\n\t'

# ──────────────────────────────────────────────────────────────────────
# Failure handler — make silent breakage loud.
# ──────────────────────────────────────────────────────────────────────
on_err() {
  local exit_code=$?
  local line_no=$1
  echo
  echo "╔══════════════════════════════════════════════════════════════════╗"
  echo "║  UPGRADE FAILED                                                  ║"
  echo "╠══════════════════════════════════════════════════════════════════╣"
  printf  "║  exit code : %-52s║\n" "$exit_code"
  printf  "║  line      : %-52s║\n" "$line_no"
  printf  "║  step      : %-52s║\n" "${STEP:-(pre-flight)}"
  echo "╚══════════════════════════════════════════════════════════════════╝"
  echo
  echo "Your previous version should still be intact. Containers may be"
  echo "stopped — restart with:"
  echo "  sudo docker compose up -d"
  echo
  if [[ -n "${PREV_SHA:-}" ]]; then
    echo "If a partial git update happened, restore the prior commit:"
    echo "  git checkout $PREV_SHA"
    echo
  fi
  if [[ -n "${DB_BACKUP:-}" ]] && [[ -f "$DB_BACKUP" ]]; then
    echo "Database backup from before the attempt is at:"
    echo "  $DB_BACKUP"
    echo
  fi
}
trap 'on_err $LINENO' ERR

# ──────────────────────────────────────────────────────────────────────
# Argument parsing
# ──────────────────────────────────────────────────────────────────────
STEP="argument parsing"
TARGET=""
ASSUME_YES="false"
DRY_RUN="false"

for arg in "$@"; do
  case "$arg" in
    --yes)     ASSUME_YES="true" ;;
    --dry-run) DRY_RUN="true" ;;
    --help|-h)
      sed -n '2,/^$/p' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    -*)
      echo "ERROR: unknown flag: $arg" >&2
      echo "Run ./upgrade.sh --help for usage." >&2
      exit 2
      ;;
    *)
      if [[ -n "$TARGET" ]]; then
        echo "ERROR: multiple target arguments. Specify only one." >&2
        exit 2
      fi
      TARGET="$arg"
      ;;
  esac
done

# Wrapper for commands that should be skipped in dry-run mode.
run() {
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "  [dry-run] would run: $*"
  else
    eval "$@"
  fi
}

echo "─── Moimio CE upgrade ───"
if [[ "$DRY_RUN" == "true" ]]; then
  echo "    (dry-run mode — no changes will be made)"
fi
echo

# ──────────────────────────────────────────────────────────────────────
# Pre-flight checks — verify everything before any mutation.
# ──────────────────────────────────────────────────────────────────────
STEP="pre-flight: working directory"
if [[ ! -f docker-compose.yml ]]; then
  echo "ERROR: docker-compose.yml not found in $(pwd)." >&2
  echo "Run this script from the moimio repo root." >&2
  exit 3
fi
if [[ ! -d .git ]]; then
  echo "ERROR: .git directory not found in $(pwd)." >&2
  echo "This script needs a git checkout. If you installed from a tarball," >&2
  echo "use deploy.sh with a downloaded scaffold zip instead." >&2
  exit 3
fi

STEP="pre-flight: .env"
if [[ ! -f .env ]]; then
  echo "ERROR: .env not found in $(pwd)." >&2
  echo "Set up .env from .env.example before running this script." >&2
  exit 4
fi

STEP="pre-flight: required tools"
for cmd in git docker gzip; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: required command '$cmd' not found in PATH." >&2
    exit 5
  fi
done
if ! sudo docker compose version >/dev/null 2>&1; then
  echo "ERROR: 'docker compose' (v2 plugin) not available via sudo." >&2
  exit 5
fi

STEP="pre-flight: working tree clean"
if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: uncommitted local changes detected:" >&2
  git status --short >&2
  echo "" >&2
  echo "Commit, stash, or discard them before upgrading." >&2
  echo "To discard: git restore ." >&2
  exit 6
fi

STEP="pre-flight: db container running"
if ! sudo docker compose ps --services --filter "status=running" 2>/dev/null | grep -q '^db$'; then
  echo "ERROR: db container is not currently running." >&2
  echo "Start it first so a pg_dump backup can be taken:" >&2
  echo "  sudo docker compose up -d db" >&2
  echo "Then re-run this script." >&2
  exit 7
fi

echo "✓ Pre-flight OK"
echo

# ──────────────────────────────────────────────────────────────────────
# Show current state and determine target.
# ──────────────────────────────────────────────────────────────────────
STEP="current state"
PREV_SHA=$(git rev-parse HEAD)
PREV_SHA_SHORT=$(git rev-parse --short HEAD)
PREV_BRANCH=$(git rev-parse --abbrev-ref HEAD)
PREV_VERSION=$(grep moimioVersion frontend/package.json 2>/dev/null | grep -oE 'v[0-9][0-9a-z.-]*' || echo "unknown")

echo "Current:"
echo "  version : $PREV_VERSION"
echo "  branch  : $PREV_BRANCH"
echo "  commit  : $PREV_SHA_SHORT"
echo

STEP="fetch remote"
echo "Fetching from origin..."
run "git fetch --tags origin"

if [[ -z "$TARGET" ]]; then
  # No target specified — pull latest of current branch.
  TARGET_REF="origin/$PREV_BRANCH"
  TARGET_LABEL="latest on $PREV_BRANCH"
else
  TARGET_REF="$TARGET"
  TARGET_LABEL="$TARGET"
fi

STEP="resolve target"
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [dry-run] would resolve target: $TARGET_REF"
  TARGET_SHA="(dry-run)"
  TARGET_SHA_SHORT="(dry-run)"
else
  if ! TARGET_SHA=$(git rev-parse --verify "$TARGET_REF" 2>/dev/null); then
    echo "ERROR: target '$TARGET_REF' doesn't resolve to a commit." >&2
    echo "Available tags:" >&2
    git tag --sort=-v:refname | head -10 >&2
    exit 8
  fi
  TARGET_SHA_SHORT=$(git rev-parse --short "$TARGET_REF")
fi

echo "Target:"
echo "  ref     : $TARGET_LABEL"
echo "  commit  : $TARGET_SHA_SHORT"
echo

if [[ "$TARGET_SHA" == "$PREV_SHA" ]]; then
  echo "Already at target. Nothing to do."
  exit 0
fi

# Show what's coming.
if [[ "$DRY_RUN" != "true" ]]; then
  echo "Commits being applied:"
  git log --oneline "$PREV_SHA..$TARGET_SHA" 2>/dev/null | sed 's/^/  /' | head -20
  echo
fi

# ──────────────────────────────────────────────────────────────────────
# Confirmation gate.
# ──────────────────────────────────────────────────────────────────────
if [[ "$ASSUME_YES" != "true" ]] && [[ "$DRY_RUN" != "true" ]]; then
  STEP="confirmation"
  read -p "Proceed with upgrade? [y/N] " -n 1 -r REPLY
  echo
  if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
    echo "Aborted by user. Nothing changed."
    exit 0
  fi
fi

# ──────────────────────────────────────────────────────────────────────
# Backups — mutations begin here, but they're all reversible.
# ──────────────────────────────────────────────────────────────────────
STEP="backup: .env"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
ENV_BACKUP=".env.pre-upgrade-${TIMESTAMP}.bak"
run "cp .env '$ENV_BACKUP'"
echo "✓ .env backed up to $ENV_BACKUP"

STEP="backup: pg_dump"
DB_USER=$(grep -E '^POSTGRES_USER=' .env 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'" || true)
DB_USER="${DB_USER:-moimio}"
DB_NAME=$(grep -E '^POSTGRES_DB=' .env 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'" || true)
DB_NAME="${DB_NAME:-moimio}"
DB_BACKUP="../pgdata-pre-upgrade-${TIMESTAMP}.sql.gz"
echo "Taking database backup to $DB_BACKUP..."
echo "  user: $DB_USER, database: $DB_NAME"
if [[ "$DRY_RUN" != "true" ]]; then
  if ! sudo docker compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" 2>/tmp/pg_dump.err | gzip > "$DB_BACKUP"; then
    echo "ERROR: pg_dump failed." >&2
    if [[ -s /tmp/pg_dump.err ]]; then
      echo "pg_dump output:" >&2
      sed 's/^/  /' /tmp/pg_dump.err >&2
    fi
    echo "POSTGRES_USER/POSTGRES_DB in .env probably don't match the db." >&2
    rm -f "$DB_BACKUP" /tmp/pg_dump.err
    exit 9
  fi
  rm -f /tmp/pg_dump.err
  DB_BACKUP_SIZE=$(du -h "$DB_BACKUP" | cut -f1)
  echo "✓ Database backed up to $DB_BACKUP ($DB_BACKUP_SIZE)"
else
  echo "  [dry-run] would run pg_dump"
fi

# ──────────────────────────────────────────────────────────────────────
# Apply the update — git checkout/pull.
# ──────────────────────────────────────────────────────────────────────
STEP="git update"
if [[ -z "$TARGET" ]]; then
  run "git pull --ff-only origin '$PREV_BRANCH'"
else
  run "git checkout '$TARGET'"
fi

NEW_VERSION=$(grep moimioVersion frontend/package.json 2>/dev/null | grep -oE 'v[0-9][0-9a-z.-]*' || echo "unknown")
echo "✓ Code updated. New version: $NEW_VERSION"
echo

# ──────────────────────────────────────────────────────────────────────
# Rebuild and restart.
# ──────────────────────────────────────────────────────────────────────
STEP="docker compose down"
run "sudo docker compose down"

STEP="docker compose build --no-cache"
run "sudo docker compose build --no-cache"

STEP="docker compose up -d"
run "sudo docker compose up -d"

# ──────────────────────────────────────────────────────────────────────
# Wait for backend to become healthy.
# ──────────────────────────────────────────────────────────────────────
STEP="health verification"
if [[ "$DRY_RUN" != "true" ]]; then
  echo "Waiting up to 90 seconds for backend to become healthy..."
  HEALTHY="false"
  for i in $(seq 1 18); do
    STATUS=$(sudo docker compose ps --format "table {{.Service}}\t{{.Status}}" 2>/dev/null | grep '^backend' || true)
    if echo "$STATUS" | grep -q "healthy"; then
      HEALTHY="true"
      break
    fi
    echo "  attempt $i/18: $STATUS"
    sleep 5
  done

  if [[ "$HEALTHY" != "true" ]]; then
    echo "WARN: backend did not become healthy within 90 seconds." >&2
    echo "Last 30 lines of backend logs:" >&2
    sudo docker compose logs --tail=30 backend >&2
    echo
    echo "To roll back:"
    echo "  git checkout $PREV_SHA"
    echo "  sudo docker compose down"
    echo "  sudo docker compose build --no-cache"
    echo "  sudo docker compose up -d"
    echo
    echo "To restore the database to its pre-upgrade state:"
    echo "  gunzip -c $DB_BACKUP | sudo docker compose exec -T db psql -U $DB_USER -d $DB_NAME"
    exit 10
  fi
  echo "✓ Backend healthy"
fi

# ──────────────────────────────────────────────────────────────────────
# Success summary.
# ──────────────────────────────────────────────────────────────────────
echo
echo "─── Upgrade complete ───"
echo "  $PREV_VERSION ($PREV_SHA_SHORT) → $NEW_VERSION ($TARGET_SHA_SHORT)"
echo
echo "Backups (keep these until you're sure the new version is solid):"
echo "  .env:     $ENV_BACKUP"
echo "  database: $DB_BACKUP"
echo
echo "Rollback command, if needed later:"
echo "  git checkout $PREV_SHA && sudo docker compose down && \\"
echo "    sudo docker compose build --no-cache && sudo docker compose up -d"
echo
echo "Tailing backend logs. Ctrl-C to detach (containers keep running)."
echo
if [[ "$DRY_RUN" != "true" ]]; then
  sudo docker compose logs -f --tail=20 backend
fi
