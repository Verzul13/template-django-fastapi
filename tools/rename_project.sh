#!/usr/bin/env bash
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <PROJECT_NAME> [API_PREFIX]"
  exit 1
fi

PN="$1"
AP="${2:-/api}"

# Update .envs/.fastapi
ENV_FILE=".envs/.fastapi"
touch "$ENV_FILE"
grep -q '^FASTAPI_PROJECT_NAME=' "$ENV_FILE" && \
  sed -i '' -e "s|^FASTAPI_PROJECT_NAME=.*$|FASTAPI_PROJECT_NAME=${PN}|" "$ENV_FILE" 2>/dev/null || \
  sed -i -e "\$aFASTAPI_PROJECT_NAME=${PN}" "$ENV_FILE"

grep -q '^FASTAPI_API_PREFIX=' "$ENV_FILE" && \
  sed -i '' -e "s|^FASTAPI_API_PREFIX=.*$|FASTAPI_API_PREFIX=${AP}|" "$ENV_FILE" 2>/dev/null || \
  sed -i -e "\$aFASTAPI_API_PREFIX=${AP}" "$ENV_FILE"

echo "Project renamed logically via ENV. Restart stack:"
echo "  docker compose up -d --build"
