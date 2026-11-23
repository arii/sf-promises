#!/usr/bin/env bash
# Mount the shared Archil disk at /mnt/archil (README "Workspace setup").
# Usage: scripts/mount_archil.sh [--read-only]
# Reads ARCHIL_MOUNT_TOKEN/ARCHIL_DISK_ID/ARCHIL_REGION from .env; never prints them.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
: "${ARCHIL_MOUNT_TOKEN:?set in .env}" "${ARCHIL_DISK_ID:?set in .env}"
MOUNT_POINT=${ARCHIL_MOUNT_POINT:-/mnt/archil}
if mountpoint -q "$MOUNT_POINT"; then
  echo "already mounted: $MOUNT_POINT"
else
  [ -d "$MOUNT_POINT" ] || sudo mkdir -p "$MOUNT_POINT"
  sudo --preserve-env=ARCHIL_MOUNT_TOKEN archil mount "$ARCHIL_DISK_ID" "$MOUNT_POINT" \
    --region "${ARCHIL_REGION:-aws-us-east-1}" --shared "$@"
fi
ls "$MOUNT_POINT/workspace"
