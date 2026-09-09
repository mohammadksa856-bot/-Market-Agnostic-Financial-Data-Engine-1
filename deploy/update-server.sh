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
$compose up -d --build --remove-orphans

container="$($compose ps -q engine)"
attempt=0
while [ "$attempt" -lt 30 ]; do
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
echo "Engine did not become healthy within 150 seconds." >&2
exit 6
