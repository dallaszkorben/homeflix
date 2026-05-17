#!/bin/bash
# ============================================================================
# HomeFlix Stop Script
#
# Tears down the HomeFlix web application by:
#   1. Stopping Apache
#   2. Unmounting all HomeFlix mounts (USB drives, tmpfs, project bind mount)
# ============================================================================

set -euo pipefail

# --- Load configuration ---
CONFIG="/home/pi/.homeflix/config.yaml"
echo "Loading configuration from $CONFIG"

WEB_ABSOLUTE_PATH=$(yq -r '.web["absolute-path"]' "$CONFIG")

# --- Stop Apache ---
echo "Stopping Apache..."
sudo systemctl stop apache2

# --- Check for processes blocking unmount ---
if lsof +D "$WEB_ABSOLUTE_PATH" 2>/dev/null | grep -v "^COMMAND" | grep -v apache2 | grep -q .; then
    echo "Error: processes are still using $WEB_ABSOLUTE_PATH:"
    lsof +D "$WEB_ABSOLUTE_PATH" 2>/dev/null | grep -v apache2
    echo "Close them (e.g. cd out of that directory, kill tail) and re-run."
    exit 1
fi

# --- Unmount all HomeFlix mounts ---
if findmnt --list -o TARGET | grep -q "^$WEB_ABSOLUTE_PATH"; then
    echo "Removing mounts..."
    while findmnt --list -o TARGET | grep -q "^$WEB_ABSOLUTE_PATH"; do
        target=$(findmnt --list -o TARGET | grep "^$WEB_ABSOLUTE_PATH" | sort -r | head -1)
        echo "  Unmounting $target"
        if ! sudo umount "$target" 2>/dev/null; then
            if ! sudo umount -l "$target" 2>&1; then
                echo "Error: could not unmount $target"
                exit 1
            fi
        fi
    done
else
    echo "No mounts to clean up."
fi

echo "HomeFlix stopped."
