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


sudo systemctl stop apache2
sudo systemctl daemon-reload

if systemctl is-active --quiet NetworkManager; then
    sudo systemctl restart NetworkManager
elif systemctl is-active --quiet networking; then
    sudo systemctl restart networking
fi

CONFIG="/home/pi/.homeflix/config.yaml"

PROJECT_PATH=$(yq -r '.project.path' "$CONFIG")
WEB_ABSOLUTE_PATH=$(yq -r '.web["absolute-path"]' "$CONFIG")
AUTOMOUNT_PATH=$(yq -r '.media["automount-path"]' "$CONFIG")
DRIVE_PATTERN=$(yq -r '.media["drive-pattern"]' "$CONFIG")
RELATIVE_PATH=$(yq -r '.media["relative-path"]' "$CONFIG")
MOUNT_TARGET="$WEB_ABSOLUTE_PATH/$RELATIVE_PATH"

# Unmount any existing mounts (children first, then the root)
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

# uncomment this line if you just want to unmount the USB drives
# exit -1

sudo mount -o bind "$PROJECT_PATH/var/www/homeflix/" "$WEB_ABSOLUTE_PATH/"

# Wait for at least one matching drive to appear (max 60 seconds)
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

# Give additional drives time to appear
sleep 10

# Create mount points on a tmpfs so we never write to the project tree
sudo mount -t tmpfs tmpfs "$MOUNT_TARGET"

# Bind-mount each matching drive as a subdirectory under MEDIA/
find "$AUTOMOUNT_PATH" -maxdepth 1 -type d -name "$DRIVE_PATTERN" | sort | while read drive; do
    name=$(basename "$drive")
    mkdir -p "$MOUNT_TARGET/$name"
    sudo mount -o bind "$drive" "$MOUNT_TARGET/$name"
done

sleep 20
sudo systemctl restart apache2
