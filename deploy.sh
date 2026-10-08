#!/bin/sh
set -eu

cd "$(dirname "$0")"
docker compose config --quiet
# Recreate Nginx to load mounted configuration and resolve the backend's current IP.
docker compose up -d --build --force-recreate
