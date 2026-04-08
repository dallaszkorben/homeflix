#!/bin/bash
# ============================================================================
# HomeFlix Startup Script
#
# Sets up the HomeFlix web application by:
#   1. Stopping Apache and restarting networking
#   2. Tearing down any leftover mounts from previous runs
#   3. Bind-mounting the project source tree onto the web server document root
#   4. Waiting for USB media drives to appear
#   5. Mounting a tmpfs isolation layer and bind-mounting each USB drive
#   6. Restarting Apache to serve the content
#
# Mount layer structure (bottom to top):
#   /var/www/homeflix/              ← bind mount of project source tree
#   /var/www/homeflix/MEDIA/        ← tmpfs (in-memory, prevents writes to source)
#   /var/www/homeflix/MEDIA/<drive> ← bind mount of each USB drive
# ============================================================================

set -euo pipefail

# --- Stop Apache ---
echo "Stopping Apache..."
sudo systemctl stop apache2
sudo systemctl daemon-reload

# --- Restart networking ---
# Ensures USB drives are discoverable after boot.
echo "Restarting networking..."
if systemctl is-active --quiet NetworkManager; then
    sudo systemctl restart NetworkManager
elif systemctl is-active --quiet networking; then
    sudo systemctl restart networking
fi

# --- Load configuration ---
CONFIG="/home/pi/.homeflix/config.yaml"
echo "Loading configuration from $CONFIG"

PROJECT_PATH=$(yq -r '.project.path' "$CONFIG")
WEB_ABSOLUTE_PATH=$(yq -r '.web["absolute-path"]' "$CONFIG")
AUTOMOUNT_PATH=$(yq -r '.media["automount-path"]' "$CONFIG")
DRIVE_PATTERN=$(yq -r '.media["drive-pattern"]' "$CONFIG")
RELATIVE_PATH=$(yq -r '.media["relative-path"]' "$CONFIG")
MOUNT_TARGET="$WEB_ABSOLUTE_PATH/$RELATIVE_PATH"

# --- Check for processes blocking unmount ---
# If shells, editors, or other tools have their cwd inside the mount point,
# unmounting will fail with "target busy". Detect this early and abort.
if lsof +D "$WEB_ABSOLUTE_PATH" 2>/dev/null | grep -v "^COMMAND" | grep -v apache2 | grep -q .; then
    echo "Error: processes are still using $WEB_ABSOLUTE_PATH:"
    lsof +D "$WEB_ABSOLUTE_PATH" 2>/dev/null | grep -v apache2
    echo "Close them (e.g. cd out of that directory, kill tail) and re-run."
    exit 1
fi

# --- Tear down previous mounts ---
# Repeated runs can stack mounts on the same path. Peel all layers from
# deepest to shallowest. Use lazy unmount (-l) as fallback for kernel-held
# stacked bind mounts that a normal unmount cannot release.
if findmnt --list -o TARGET | grep -q "^$WEB_ABSOLUTE_PATH"; then
    echo "Removing leftover mounts..."
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
    echo "No previous mounts to clean up."
fi

# Uncomment to stop here (unmount only, no remount):
# exit 0

# --- Bind-mount project source tree onto the web server document root ---
echo "Mounting project tree: $PROJECT_PATH/var/www/homeflix/ -> $WEB_ABSOLUTE_PATH/"
sudo mount -o bind "$PROJECT_PATH/var/www/homeflix/" "$WEB_ABSOLUTE_PATH/"

# --- Wait for USB media drives ---
# The OS automounts USB drives at AUTOMOUNT_PATH using the drive's filesystem
# label as the folder name. Wait until at least one drive matching
# DRIVE_PATTERN appears (up to 60 seconds).
echo "Waiting for USB drives matching '$DRIVE_PATTERN' at $AUTOMOUNT_PATH (up to 60s)..."
TIMEOUT=60
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    FOUND=$(find "$AUTOMOUNT_PATH" -maxdepth 1 -type d -name "$DRIVE_PATTERN" 2>/dev/null)
    if [ -n "$FOUND" ]; then
        echo "  Drive(s) detected after ${ELAPSED}s."
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

if [ -z "$FOUND" ]; then
    echo "  Warning: no drives found after ${TIMEOUT}s — continuing without USB media."
fi

# Allow extra time for additional drives to be automounted.
echo "Waiting 10s for additional drives..."
sleep 10

# --- Mount tmpfs isolation layer ---
# Without this, mkdir would create directories in the project source tree
# (via the bind mount), polluting the repo. The tmpfs is in-memory — any
# directories created here vanish automatically when unmounted.
echo "Mounting tmpfs isolation layer at $MOUNT_TARGET"
sudo mount -t tmpfs tmpfs "$MOUNT_TARGET"

# --- Bind-mount each USB media drive ---
DRIVE_COUNT=0
for drive in $(find "$AUTOMOUNT_PATH" -maxdepth 1 -type d -name "$DRIVE_PATTERN" | sort); do
    name=$(basename "$drive")
    echo "  Mounting USB drive: $drive -> $MOUNT_TARGET/$name"
    mkdir -p "$MOUNT_TARGET/$name"
    sudo mount -o bind "$drive" "$MOUNT_TARGET/$name"
    DRIVE_COUNT=$((DRIVE_COUNT + 1))
done
echo "Mounted $DRIVE_COUNT USB drive(s)."

# --- Restart Apache ---
echo "Waiting 20s for mounts to stabilize..."
sleep 20
echo "Starting Apache..."
sudo systemctl restart apache2

echo "HomeFlix is ready."
