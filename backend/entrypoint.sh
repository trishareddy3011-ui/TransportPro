#!/bin/sh
set -e

echo "=================================================="
echo " Starting VahanOne Backend Container "
echo "=================================================="

# Wait for PostgreSQL to be ready
echo "==> Waiting for database connection..."
python - <<'EOF'
import os
import sys
import time
from urllib.parse import urlparse
import psycopg

raw_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgrespassword@db:5432/vahanone_db")
if raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql://", 1)
elif raw_url.startswith("postgresql+psycopg2://"):
    raw_url = raw_url.replace("postgresql+psycopg2://", "postgresql://", 1)
elif raw_url.startswith("postgresql+psycopg://"):
    raw_url = raw_url.replace("postgresql+psycopg://", "postgresql://", 1)

retries = 30
while retries > 0:
    try:
        conn = psycopg.connect(raw_url, connect_timeout=3)
        conn.close()
        print("==> Database connection established successfully.")
        sys.exit(0)
    except Exception as e:
        retries -= 1
        print(f"Waiting for database... ({retries} retries left): {e}")
        time.sleep(2)

print("ERROR: Could not connect to database after 60s.")
sys.exit(1)
EOF

echo "==> Applying database migrations (alembic upgrade head)..."
alembic upgrade head

if [ "${SEED_DEMO_DATA:-true}" = "true" ] || [ "${SEED_DEMO_DATA:-true}" = "1" ]; then
    echo "==> Seeding demo data..."
    python seed_demo_data.py || echo "Notice: Demo data seed completed or already present."
fi

echo "==> Starting FastAPI application on port 8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
