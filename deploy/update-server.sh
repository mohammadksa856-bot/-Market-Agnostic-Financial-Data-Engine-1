#!/bin/sh
set -eu

project_dir="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$project_dir"

if [ ! -f .env ]; then
    echo "Missing $project_dir/.env; copy .env.example and set production secrets." >&2
    exit 2
fi

if command -v flock >/dev/null 2>&1; then
    exec 9>"${TMPDIR:-/tmp}/finengine-deploy.lock"
    flock -n 9 || { echo "Another deployment is already running." >&2; exit 3; }
fi

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "Refusing deployment because tracked files on the server were modified." >&2
    exit 4
fi

git fetch origin main
git checkout main
git pull --ff-only origin main

compose="docker compose -f compose.yaml -f compose.production.yaml"
$compose config --quiet
extra_workers="${FINENGINE_EXTRA_WORKERS:-0}"
case "$extra_workers" in
    ''|*[!0-9]*)
        echo "FINENGINE_EXTRA_WORKERS must be a non-negative integer." >&2
        exit 7
        ;;
esac
if [ "$extra_workers" -gt 0 ]; then
    # Extra workers use the queue's atomic leases and independent SQLite
    # connections. Keep the count explicitly bounded by the operator instead of
    # letting Compose or host CPU count choose an unsafe level automatically.
    $compose --profile extra-writer up -d --build --remove-orphans \
        --scale worker="$extra_workers"
else
    $compose up -d --build --remove-orphans
fi

container="$($compose ps -q engine)"
attempt=0
health_attempts="${FINENGINE_DEPLOY_HEALTH_ATTEMPTS:-180}"
while [ "$attempt" -lt "$health_attempts" ]; do
    status="$(docker inspect --format '{{.State.Health.Status}}' "$container" 2>/dev/null || true)"
    if [ "$status" = "healthy" ]; then
        $compose ps
        exit 0
    fi
    if [ "$status" = "unhealthy" ]; then
        $compose logs --tail=100 engine
        exit 5
    fi
    attempt=$((attempt + 1))
    sleep 5
done

$compose logs --tail=100 engine
echo "Engine did not become healthy within $((health_attempts * 5)) seconds." >&2
exit 6
