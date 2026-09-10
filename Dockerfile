FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md /tmp/finengine-deps/
RUN python -m pip install --no-cache-dir --upgrade pip \
    && mkdir -p /tmp/finengine-deps/src/finengine \
    && touch /tmp/finengine-deps/src/finengine/__init__.py \
    && python -m pip install --no-cache-dir -e "/tmp/finengine-deps[agents]" \
    && python -m playwright install --with-deps chromium \
    && apt-get update \
    && apt-get install -y --no-install-recommends xauth \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN python -m pip install --no-cache-dir --no-deps -e . \
    && chmod +x /app/deploy/start-production.sh /app/deploy/refresh-universe.sh \
        /app/deploy/sync-supabase.sh /app/deploy/update-server.sh \
        /app/deploy/preflight.sh /app/deploy/backup-loop.sh /app/deploy/onboarding-loop.sh \
        /app/deploy/historical-backfill-loop.sh

EXPOSE 8000
VOLUME ["/app/state"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000/health', method='HEAD'), timeout=4)" || exit 1

CMD ["/app/deploy/start-production.sh"]
