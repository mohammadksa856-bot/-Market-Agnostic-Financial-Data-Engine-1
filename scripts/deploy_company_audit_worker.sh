#!/bin/sh
set -eu
# Run on the authorized AWS host. This changes only the dedicated audit container.
runtime=/var/lib/financial-data-engine/audit-runtime
test -f "$runtime/company_audit_worker.py"
test -f "$runtime/company_audit_health.py"
if docker inspect finengine-audit-1 >/dev/null 2>&1; then
    test "$(docker inspect finengine-audit-1 --format '{{.Config.Image}}')" = repo-engine
    docker stop -t 20 finengine-audit-1
    docker rm finengine-audit-1
fi
docker run -d --name finengine-audit-1 --restart unless-stopped \
    --cpus 0.35 --memory 768m --pids-limit 64 --network none --read-only \
    --cap-drop ALL --security-opt no-new-privileges --tmpfs /tmp:rw,size=128m \
    --log-opt max-size=10m --log-opt max-file=3 \
    --health-cmd 'python /audit/company_audit_health.py' \
    --health-interval 30s --health-timeout 10s --health-start-period 180s --health-retries 3 \
    -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONUNBUFFERED=1 \
    -v /var/lib/financial-data-engine:/app/state:ro \
    -v /var/lib/financial-data-engine/reports:/app/state/reports:rw \
    -v "$runtime":/audit:ro \
    -v /var/lib/financial-data-engine/seed-raw:/app/data/raw:ro \
    --entrypoint python repo-engine /audit/company_audit_worker.py
