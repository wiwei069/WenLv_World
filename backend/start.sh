#!/bin/bash
set -e
echo "Starting uvicorn..."
cd /opt/render/project/src/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
