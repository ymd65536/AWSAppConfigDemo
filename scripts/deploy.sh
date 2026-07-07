#!/usr/bin/env bash
set -euo pipefail

STACK_NAME="${STACK_NAME:-aws-appconfig-demo}"
AWS_REGION="${AWS_REGION:-ap-northeast-1}"

PROFILE_ARGS=()
if [[ -n "${AWS_PROFILE:-}" ]]; then
  PROFILE_ARGS=(--profile "$AWS_PROFILE")
fi

echo "Building SAM application..."
echo "Lambda dependencies are resolved from requirements.txt during sam build."
sam build

echo "Deploying stack '$STACK_NAME' to region '$AWS_REGION'..."
sam deploy \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
  --no-confirm-changeset \
  "${PROFILE_ARGS[@]}"
