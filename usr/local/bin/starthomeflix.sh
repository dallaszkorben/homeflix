# sudo systemctl stop apache2
# sudo systemctl daemon-reload
#
# if systemctl is-active --quiet NetworkManager; then
#     sudo systemctl restart NetworkManager
# elif systemctl is-active --quiet networking; then
#     sudo systemctl restart networking
# fi
#
# CONFIG="/home/pi/.homeflix/config.yaml"
#
# PROJECT_PATH=$(yq -r '.project.path' "$CONFIG")
# WEB_ABSOLUTE_PATH=$(yq -r '.web["absolute-path"]' "$CONFIG")
#
# # Unmount any existing mounts (children first, then the root)
# findmnt --list -o TARGET | grep "^$WEB_ABSOLUTE_PATH/" | sort -r | while read mnt; do
#     if ! sudo umount "$mnt" 2>&1; then
#         echo "Warning: could not unmount $mnt"
#     fi
# done
# while findmnt --list -o TARGET | grep -q "^$WEB_ABSOLUTE_PATH$"; do
#     if ! sudo umount "$WEB_ABSOLUTE_PATH" 2>&1; then
#         echo "Warning: could not unmount $WEB_ABSOLUTE_PATH (target busy)"
#         break
#     fi
# done
#
# # # Clean up empty mount-point directories left behind by previous runs
# # MOUNT_TARGET="$WEB_ABSOLUTE_PATH/$RELATIVE_PATH"
# # if [ -d "$MOUNT_TARGET" ]; then
# #     find "$MOUNT_TARGET" -maxdepth 1 -mindepth 1 -type d -empty -delete 2>/dev/null
# # fi
#
# # uncomment this line if you just want to unmount the USB drives
# # exit -1
#
# sudo mount -o bind "$PROJECT_PATH/var/www/homeflix/" "$WEB_ABSOLUTE_PATH/"
#
# AUTOMOUNT_PATH=$(yq -r '.media["automount-path"]' "$CONFIG")
# DRIVE_PATTERN=$(yq -r '.media["drive-pattern"]' "$CONFIG")
# RELATIVE_PATH=$(yq -r '.media["relative-path"]' "$CONFIG")
# MOUNT_TARGET="$WEB_ABSOLUTE_PATH/$RELATIVE_PATH"
#
# # Wait for at least one matching drive to appear (max 60 seconds)
# TIMEOUT=60
# ELAPSED=0
# while [ $ELAPSED -lt $TIMEOUT ]; do
#     FOUND=$(find "$AUTOMOUNT_PATH" -maxdepth 1 -type d -name "$DRIVE_PATTERN" 2>/dev/null)
#     if [ -n "$FOUND" ]; then
#         break
#     fi
#     sleep 2
#     ELAPSED=$((ELAPSED + 2))
# done
#
# # Give additional drives time to appear
# sleep 10
#
# # Bind-mount each matching drive as a subdirectory under MEDIA/
# find "$AUTOMOUNT_PATH" -maxdepth 1 -type d -name "$DRIVE_PATTERN" | sort | while read drive; do
#     name=$(basename "$drive")
#     mkdir -p "$MOUNT_TARGET/$name"
#     sudo mount -o bind "$drive" "$MOUNT_TARGET/$name"
# done
#
# sleep 20
# sudo systemctl restart apache2


# sudo systemctl stop apache2
# sudo systemctl daemon-reload
#
# if systemctl is-active --quiet NetworkManager; then
#     sudo systemctl restart NetworkManager
# elif systemctl is-active --quiet networking; then
#     sudo systemctl restart networking
# fi
#
# CONFIG="/home/pi/.homeflix/config.yaml"
#
# PROJECT_PATH=$(yq -r '.project.path' "$CONFIG")
# WEB_ABSOLUTE_PATH=$(yq -r '.web["absolute-path"]' "$CONFIG")
# AUTOMOUNT_PATH=$(yq -r '.media["automount-path"]' "$CONFIG")
# DRIVE_PATTERN=$(yq -r '.media["drive-pattern"]' "$CONFIG")
# RELATIVE_PATH=$(yq -r '.media["relative-path"]' "$CONFIG")
# MOUNT_TARGET="$WEB_ABSOLUTE_PATH/$RELATIVE_PATH"
#
# # Unmount any existing mounts (children first, then the root)
# findmnt --list -o TARGET | grep "^$WEB_ABSOLUTE_PATH/" | sort -r | while read mnt; do
#     if ! sudo umount "$mnt" 2>&1; then
#         echo "Warning: could not unmount $mnt"
#     fi
# done
# while findmnt --list -o TARGET | grep -q "^$WEB_ABSOLUTE_PATH$"; do
#     if ! sudo umount "$WEB_ABSOLUTE_PATH" 2>&1; then
#         echo "Warning: could not unmount $WEB_ABSOLUTE_PATH (target busy)"
#         break
#     fi
# done
#
# # Clean up empty mount-point directories left behind by previous runs
# if [ -d "$MOUNT_TARGET" ]; then
#     find "$MOUNT_TARGET" -maxdepth 1 -mindepth 1 -type d -empty -delete 2>/dev/null
# fi
#
# # uncomment this line if you just want to unmount the USB drives
# # exit -1
#
# sudo mount -o bind "$PROJECT_PATH/var/www/homeflix/" "$WEB_ABSOLUTE_PATH/"
#
# # Wait for at least one matching drive to appear (max 60 seconds)
# TIMEOUT=60
# ELAPSED=0
# while [ $ELAPSED -lt $TIMEOUT ]; do
#     FOUND=$(find "$AUTOMOUNT_PATH" -maxdepth 1 -type d -name "$DRIVE_PATTERN" 2>/dev/null)
#     if [ -n "$FOUND" ]; then
#         break
#     fi
#     sleep 2
#     ELAPSED=$((ELAPSED + 2))
# done
#
# # Give additional drives time to appear
# sleep 10
#
# # Bind-mount each matching drive as a subdirectory under MEDIA/
# find "$AUTOMOUNT_PATH" -maxdepth 1 -type d -name "$DRIVE_PATTERN" | sort | while read drive; do
#     name=$(basename "$drive")
#     mkdir -p "$MOUNT_TARGET/$name"
#     sudo mount -o bind "$drive" "$MOUNT_TARGET/$name"
# done
#
# sleep 20
# sudo systemctl restart apache2


# sudo systemctl stop apache2
# sudo systemctl daemon-reload
#
# if systemctl is-active --quiet NetworkManager; then
#     sudo systemctl restart NetworkManager
# elif systemctl is-active --quiet networking; then
#     sudo systemctl restart networking
# fi
#
# CONFIG="/home/pi/.homeflix/config.yaml"
#
# PROJECT_PATH=$(yq -r '.project.path' "$CONFIG")
# WEB_ABSOLUTE_PATH=$(yq -r '.web["absolute-path"]' "$CONFIG")
# AUTOMOUNT_PATH=$(yq -r '.media["automount-path"]' "$CONFIG")
# DRIVE_PATTERN=$(yq -r '.media["drive-pattern"]' "$CONFIG")
# RELATIVE_PATH=$(yq -r '.media["relative-path"]' "$CONFIG")
# MOUNT_TARGET="$WEB_ABSOLUTE_PATH/$RELATIVE_PATH"
#
# # Unmount any existing mounts (children first, then the root)
# findmnt --list -o TARGET | grep "^$WEB_ABSOLUTE_PATH/" | sort -r | while read mnt; do
#     if ! sudo umount "$mnt" 2>&1; then
#         echo "Warning: could not unmount $mnt"
#     fi
# done
# while findmnt --list -o TARGET | grep -q "^$WEB_ABSOLUTE_PATH$"; do
#     if ! sudo umount "$WEB_ABSOLUTE_PATH" 2>&1; then
#         echo "Warning: could not unmount $WEB_ABSOLUTE_PATH (target busy)"
#         break
#     fi
# done
#
# # uncomment this line if you just want to unmount the USB drives
# # exit -1
#
# sudo mount -o bind "$PROJECT_PATH/var/www/homeflix/" "$WEB_ABSOLUTE_PATH/"
#
# # Wait for at least one matching drive to appear (max 60 seconds)
# TIMEOUT=60
# ELAPSED=0
# while [ $ELAPSED -lt $TIMEOUT ]; do
#     FOUND=$(find "$AUTOMOUNT_PATH" -maxdepth 1 -type d -name "$DRIVE_PATTERN" 2>/dev/null)
#     if [ -n "$FOUND" ]; then
#         break
#     fi
#     sleep 2
#     ELAPSED=$((ELAPSED + 2))
# done
#
# # Give additional drives time to appear
# sleep 10
#
# # Create mount points on a tmpfs so we never write to the project tree
# sudo mount -t tmpfs tmpfs "$MOUNT_TARGET"
#
# # Bind-mount each matching drive as a subdirectory under MEDIA/
# find "$AUTOMOUNT_PATH" -maxdepth 1 -type d -name "$DRIVE_PATTERN" | sort | while read drive; do
#     name=$(basename "$drive")
#     mkdir -p "$MOUNT_TARGET/$name"
#     sudo mount -o bind "$drive" "$MOUNT_TARGET/$name"
# done
#
# sleep 20
# sudo systemctl restart apache2


# ============================================================================
# HomeFlix Startup Script
#
# This script sets up the HomeFlix web application by:
#   1. Restarting network and web services
#   2. Bind-mounting the project source tree onto the web server document root
#   3. Mounting USB media drives so their content is accessible via the web UI
#
# Mount layer structure (bottom to top):
#   /var/www/homeflix/              ← bind mount of project source tree
#   /var/www/homeflix/MEDIA/        ← tmpfs (in-memory, prevents writes to source tree)
#   /var/www/homeflix/MEDIA/<drive> ← bind mount of each USB drive
# ============================================================================

# Stop Apache before reconfiguring mounts — avoids serving stale/partial content
sudo systemctl stop apache2
sudo systemctl daemon-reload

# Restart networking to ensure USB drives are discoverable after boot
if systemctl is-active --quiet NetworkManager; then
    sudo systemctl restart NetworkManager
elif systemctl is-active --quiet networking; then
    sudo systemctl restart networking
fi

# --- Load configuration ---
CONFIG="/home/pi/.homeflix/config.yaml"

PROJECT_PATH=$(yq -r '.project.path' "$CONFIG")
WEB_ABSOLUTE_PATH=$(yq -r '.web["absolute-path"]' "$CONFIG")
AUTOMOUNT_PATH=$(yq -r '.media["automount-path"]' "$CONFIG")
DRIVE_PATTERN=$(yq -r '.media["drive-pattern"]' "$CONFIG")
RELATIVE_PATH=$(yq -r '.media["relative-path"]' "$CONFIG")
MOUNT_TARGET="$WEB_ABSOLUTE_PATH/$RELATIVE_PATH"

# --- Tear down previous mounts ---
# Unmount in reverse order (deepest paths first) to avoid "target busy" errors.
# This handles leftover mounts from a previous run or a crashed restart.
findmnt --list -o TARGET | grep "^$WEB_ABSOLUTE_PATH/" | sort -r | while read mnt; do
    if ! sudo umount "$mnt" 2>&1; then
        echo "Warning: could not unmount $mnt"
    fi
done
while findmnt --list -o TARGET | grep -q "^$WEB_ABSOLUTE_PATH$"; do
    if ! sudo umount "$WEB_ABSOLUTE_PATH" 2>&1; then
        echo "Warning: could not unmount $WEB_ABSOLUTE_PATH (target busy)"
        break
    fi
done

# Uncomment this line if you just want to unmount and stop (no remount)
# exit -1

# --- Set up the web document root ---
# Bind-mount the project source tree onto the web server path so Apache
# serves files directly from the development/project directory.
sudo mount -o bind "$PROJECT_PATH/var/www/homeflix/" "$WEB_ABSOLUTE_PATH/"

# --- Wait for USB media drives ---
# The OS automounts USB drives at AUTOMOUNT_PATH (e.g. /media/akoel/) using
# the drive's filesystem label as the folder name. Wait until at least one
# drive matching DRIVE_PATTERN (e.g. "MEDIA*") appears.
TIMEOUT=60
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    FOUND=$(find "$AUTOMOUNT_PATH" -maxdepth 1 -type d -name "$DRIVE_PATTERN" 2>/dev/null)
    if [ -n "$FOUND" ]; then
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

# Allow extra time for additional drives to be automounted
sleep 10

# --- Mount tmpfs as an isolation layer ---
# Without this, mkdir below would create directories in the project source tree
# (via the bind mount), polluting the git repo with leftover empty folders
# that persist after unmounting. The tmpfs is an in-memory filesystem — any
# directories created here vanish automatically when unmounted.
sudo mount -t tmpfs tmpfs "$MOUNT_TARGET"

# --- Bind-mount each USB media drive ---
# For each automounted drive matching the pattern, create a subdirectory on
# the tmpfs and bind-mount the drive there. This makes drive content accessible
# at e.g. /var/www/homeflix/MEDIA/MEDIA, /var/www/homeflix/MEDIA/MEDIA-SERIES-1
find "$AUTOMOUNT_PATH" -maxdepth 1 -type d -name "$DRIVE_PATTERN" | sort | while read drive; do
    name=$(basename "$drive")
    mkdir -p "$MOUNT_TARGET/$name"
    sudo mount -o bind "$drive" "$MOUNT_TARGET/$name"
done

# Wait for mounts to stabilize before restarting Apache
sleep 20
sudo systemctl restart apache2


