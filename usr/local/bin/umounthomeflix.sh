# ============================================================================
# HomeFlix Unmount Script
#
# Tears down the HomeFlix mount stack in the correct order:
#   1. Stop Apache so nothing is using the mounted paths
#   2. Unmount USB drive bind mounts  (deepest layer)
#   3. Unmount the tmpfs on MEDIA/    (middle layer)
#   4. Unmount the project bind mount (base layer)
#
# The tmpfs layer and all mount-point directories it held vanish automatically
# on unmount — nothing is left behind on disk or in the project source tree.
# ============================================================================

# Stop Apache to release any open file handles on the mounted paths
sudo systemctl stop apache2

CONFIG="/home/pi/.homeflix/config.yaml"
WEB_ABSOLUTE_PATH=$(yq -r '.web["absolute-path"]' "$CONFIG")

# Unmount all layers under the web root, deepest paths first.
# This ensures child mounts (USB drives) are removed before their parents
# (tmpfs, project bind mount), avoiding "target busy" errors.
findmnt --list -o TARGET | grep "^$WEB_ABSOLUTE_PATH/" | sort -r | while read mnt; do
    if ! sudo umount "$mnt" 2>&1; then
        echo "Warning: could not unmount $mnt"
    fi
done

# Unmount the web root bind mount itself
while findmnt --list -o TARGET | grep -q "^$WEB_ABSOLUTE_PATH$"; do
    if ! sudo umount "$WEB_ABSOLUTE_PATH" 2>&1; then
        echo "Warning: could not unmount $WEB_ABSOLUTE_PATH (target busy)"
        break
    fi
done

echo "HomeFlix unmounted."