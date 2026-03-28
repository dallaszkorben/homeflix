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

# Bind-mount the project to the web root
sudo mount -o bind /home/pi/Projects/python/homeflix/var/www/homeflix/ /var/www/homeflix/

RELATIVE_PATH=$(yq -r '.media["relative-path"]' /home/pi/.homeflix/config.yaml)
MOUNT_TARGET="/var/www/homeflix/$RELATIVE_PATH"

# Wait for at least one MEDIA* drive to appear (max 60 seconds)
TIMEOUT=60
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    FOUND=$(find /media/pi -maxdepth 1 -type d -name 'MEDIA*' 2>/dev/null)
    if [ -n "$FOUND" ]; then
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

# Collect all MEDIA* drives into a colon-separated list
MERGE_PATHS=$(find /media/pi -maxdepth 1 -type d -name 'MEDIA*' 2>/dev/null | sort | tr '\n' ':' | sed 's/:$//')

if [ -n "$MERGE_PATHS" ]; then
    sudo mergerfs -o defaults,allow_other,use_ino,category.create=mfs "$MERGE_PATHS" "$MOUNT_TARGET"
fi

sleep 20
sudo systemctl restart apache2