#!/bin/bash
set -e

echo "TechMentor AI — starting up..."

# Apply schema (idempotent)
python scripts/init_db.py

# Seed problems if DB is fresh
python scripts/seed_db.py 2>/dev/null || true

# Launch Streamlit
exec streamlit run src/app.py \
    --server.port=${APP_PORT:-8501} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
