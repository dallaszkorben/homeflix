sudo systemctl stop apache2

# I got an error before: mount: (hint) your fstab has been modified, but systemd still uses the old version; use  to reload
sudo systemctl daemon-reload

# reload the /etc/network/interfaces
sudo systemctl restart networking
ABSOLUTE_PATH=$(yq -r '.media["absolute-path"]' /home/pi/.homeflix/config.yaml)
RELATIVE_PATH=$(yq -r '.media["relative-path"]' /home/pi/.homeflix/config.yaml)
sudo mount -o bind /home/pi/Projects/python/homeflix/var/www/homeflix/ /var/www/homeflix/
sleep 20
sudo mount -o bind $ABSOLUTE_PATH /var/www/homeflix/$RELATIVE_PATH/
sleep 20
sudo systemctl restart apache2
