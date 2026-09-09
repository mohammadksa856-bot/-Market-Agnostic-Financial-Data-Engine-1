#!/bin/sh
set -u

# Read-only production-host readiness check. Run after copying .env and before
# the first deploy. It deliberately reports every problem in one pass.
project_dir="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
env_file="${1:-$project_dir/.env}"
failures=0
warnings=0

fail() { printf 'FAIL: %s\n' "$*" >&2; failures=$((failures + 1)); }
warn() { printf 'WARN: %s\n' "$*" >&2; warnings=$((warnings + 1)); }
pass() { printf 'PASS: %s\n' "$*"; }

[ "$(uname -s 2>/dev/null || true)" = "Linux" ] \
    && pass "Linux host" || fail "a Linux host is required"

for command_name in git docker; do
    command -v "$command_name" >/dev/null 2>&1 \
        && pass "$command_name is installed" || fail "$command_name is not installed"
done
if command -v docker >/dev/null 2>&1; then
    docker compose version >/dev/null 2>&1 \
        && pass "Docker Compose v2 is available" || fail "Docker Compose v2 is required"
    docker info >/dev/null 2>&1 \
        && pass "Docker daemon is reachable" || fail "Docker daemon is not reachable by this user"
fi

cpu_count="$(getconf _NPROCESSORS_ONLN 2>/dev/null || printf '0')"
[ "$cpu_count" -ge 4 ] 2>/dev/null \
    && pass "$cpu_count CPU threads available" || warn "4 CPU threads recommended; found $cpu_count"
memory_kib="$(awk '/^MemTotal:/ {print $2}' /proc/meminfo 2>/dev/null || printf '0')"
[ "$memory_kib" -ge 7340032 ] 2>/dev/null \
    && pass "at least 7 GiB RAM available" || warn "8 GiB RAM recommended"

if [ ! -f "$env_file" ]; then
    fail "missing $env_file (copy .env.example and replace every placeholder)"
else
    set -a
    # shellcheck disable=SC1090
    . "$env_file"
    set +a

    case "${SEC_USER_AGENT:-}" in
        *"@"*) pass "SEC_USER_AGENT contains a monitored contact" ;;
        *) fail "SEC_USER_AGENT must contain a monitored email address" ;;
    esac
    case "${SEC_USER_AGENT:-}" in *example.com*) fail "replace the SEC_USER_AGENT example address" ;; esac
    api_key="${FINENGINE_API_KEY:-}"
    [ "${#api_key}" -ge 32 ] 2>/dev/null \
        && pass "FINENGINE_API_KEY length is acceptable" \
        || fail "FINENGINE_API_KEY must be at least 32 characters"
    case "${API_DOMAIN:-}" in
        ""|api.example.com) fail "set API_DOMAIN to the real DNS name" ;;
        *) pass "API_DOMAIN is set" ;;
    esac

    for variable_name in FINENGINE_STATE_DIR FINENGINE_BACKUP_DIR; do
        eval "directory=\${$variable_name:-}"
        case "$directory" in
            /*) ;;
            *) fail "$variable_name must be an absolute server path"; continue ;;
        esac
        if [ -d "$directory" ] && [ -w "$directory" ]; then
            pass "$variable_name exists and is writable"
        else
            fail "$variable_name must exist and be writable: $directory"
        fi
    done

    disk_path="${FINENGINE_STATE_DIR:-/}"
    if [ -d "$disk_path" ]; then
        free_kib="$(df -Pk "$disk_path" | awk 'NR==2 {print $4}')"
        if [ "${free_kib:-0}" -ge 157286400 ] 2>/dev/null; then
            pass "at least 150 GiB free on the state volume"
        elif [ "${free_kib:-0}" -ge 20971520 ] 2>/dev/null; then
            warn "less than 150 GiB free; acceptable only for a bounded pilot"
        else
            fail "less than 20 GiB free on the state volume"
        fi
    fi

    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        (cd "$project_dir" && docker compose -f compose.yaml -f compose.production.yaml config --quiet) \
            && pass "production Compose configuration is valid" \
            || fail "production Compose configuration is invalid"
    fi
fi

printf 'Preflight complete: %s failure(s), %s warning(s).\n' "$failures" "$warnings"
[ "$failures" -eq 0 ]
