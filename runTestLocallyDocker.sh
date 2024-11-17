#!/bin/bash

# Make sure the files are properly permissioned
chmod 600 .secrets .env

# Create a temporary file for the secrets that will be automatically cleaned up
temp_secrets=$(mktemp)
trap 'rm -f "$temp_secrets"' EXIT

# Create secrets file in secure temp location
cat > "$temp_secrets" <<EOF
GH_COMMIT_TOKEN=$(cat .secrets)
EOF

# Run act with temporary secrets file
act workflow_dispatch \
  -W .github/workflows/test.yml \
  --eventpath workflow_dispatch.json \
  --bind \
  -P ubuntu-latest=catthehacker/ubuntu:act-latest \
  --container-architecture linux/amd64 \
  --container-daemon-socket /var/run/docker.sock \
  --secret-file "$temp_secrets" \
  --env-file .env