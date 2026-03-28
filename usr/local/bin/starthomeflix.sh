# sudo systemctl stop apache2
#
# # I got an error before: mount: (hint) your fstab has been modified, but systemd still uses the old version; use  to reload
# sudo systemctl daemon-reload
#
# # reload the /etc/network/interfaces
# sudo systemctl restart networking
# ABSOLUTE_PATH=$(yq -r '.media["absolute-path"]' /home/pi/.homeflix/config.yaml)
# RELATIVE_PATH=$(yq -r '.media["relative-path"]' /home/pi/.homeflix/config.yaml)
# sudo mount -o bind /home/pi/Projects/python/homeflix/var/www/homeflix/ /var/www/homeflix/
# sleep 20
# sudo mount -o bind $ABSOLUTE_PATH /var/www/homeflix/$RELATIVE_PATH/
# sleep 20
# sudo systemctl restart apache2

sudo systemctl stop apache2
sudo systemctl daemon-reload
sudo systemctl restart networking

sudo mount -o bind /home/pi/Projects/python/homeflix/var/www/homeflix/ /var/www/homeflix/

AUTOMOUNT_PATH=$(yq -r '.media["automount-path"]' /home/pi/.homeflix/config.yaml)
DRIVE_PATTERN=$(yq -r '.media["drive-pattern"]' /home/pi/.homeflix/config.yaml)
RELATIVE_PATH=$(yq -r '.media["relative-path"]' /home/pi/.homeflix/config.yaml)
MOUNT_TARGET="/var/www/homeflix/$RELATIVE_PATH"

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

# Bind-mount each matching drive as a subdirectory under MEDIA/
find "$AUTOMOUNT_PATH" -maxdepth 1 -type d -name "$DRIVE_PATTERN" | sort | while read drive; do
    name=$(basename "$drive")
    mkdir -p "$MOUNT_TARGET/$name"
    sudo mount -o bind "$drive" "$MOUNT_TARGET/$name"
done

sleep 20
sudo systemctl restart apache2
