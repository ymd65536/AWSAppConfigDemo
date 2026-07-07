#!/bin/sh
set -eu
exec python3 -m uvicorn app.step4_bedrock:app --host 0.0.0.0 --port "${PORT:-8080}"
