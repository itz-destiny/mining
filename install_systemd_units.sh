
#!/usr/bin/env bash
# install_systemd_units.sh
# Usage: sudo ./install_systemd_units.sh
# This script installs the provided systemd unit templates into /etc/systemd/system,
# sets permissions, reloads systemd, enables and starts the services.
# Review the unit files mining-backend.service and mining-stratum.service before running.
set -euo pipefail

PROJ_DIR="$(cd "$(dirname "$0")" && pwd)"
UNIT_DIR="/etc/systemd/system"

BACKEND_UNIT_SRC="$PROJ_DIR/mining-backend.service"
STRATUM_UNIT_SRC="$PROJ_DIR/mining-stratum.service"

if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run as root (sudo)."
  exit 1
fi

if [ ! -f "$BACKEND_UNIT_SRC" ] || [ ! -f "$STRATUM_UNIT_SRC" ]; then
  echo "Unit files not found in project root. Expected:"
  echo "  $BACKEND_UNIT_SRC"
  echo "  $STRATUM_UNIT_SRC"
  exit 1
fi

# Back up existing units if present
if [ -f "$UNIT_DIR/mining-backend.service" ]; then
  cp "$UNIT_DIR/mining-backend.service" "$UNIT_DIR/mining-backend.service.bak.$(date +%s)"
fi
if [ -f "$UNIT_DIR/mining-stratum.service" ]; then
  cp "$UNIT_DIR/mining-stratum.service" "$UNIT_DIR/mining-stratum.service.bak.$(date +%s)"
fi

# Copy unit files
cp "$BACKEND_UNIT_SRC" "$UNIT_DIR/"
cp "$STRATUM_UNIT_SRC" "$UNIT_DIR/"

# Set permissions
chmod 644 "$UNIT_DIR/mining-backend.service"
chmod 644 "$UNIT_DIR/mining-stratum.service"

# Reload systemd, enable and start services
systemctl daemon-reload
systemctl enable mining-backend.service --now
systemctl enable mining-stratum.service --now

echo "Services installed and started. Check status with:"
echo "  systemctl status mining-backend.service"
echo "  systemctl status mining-stratum.service"
