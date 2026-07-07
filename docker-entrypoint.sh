#!/usr/bin/env bash
set -euo pipefail

exec /opt/aws-lambda-adapter --port "$PORT" -- uvicorn app.step4_bedrock:app --host 0.0.0.0 --port "$PORT"
