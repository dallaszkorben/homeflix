# playem
web media player


## Prepare Raspberry Pi 4 


~~
### Install python 3.7
```sh
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.7
sudo rm /usr/bin/python3
sudo ln -s /usr/bin/python3.7 /usr/bin/python3
```

### Get rid of the old python 
```sh
sudo apt-get update
sudo apt-get upgrade

sudo apt -s remove python2.7
sudo apt -s remove python2
sudo apt-get autoremove
```

## Get rid of the old pip 
```sh
sudo apt remove python3-pip
sudo apt install python3-pip
```
~~


## Install python 3.10 
```sh
sudo apt update && sudo apt upgrade -y
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.10
python3.10 --version
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10
python3.10 -m pip --version
python3.10 -m pip install --upgrade pip
sudo apt install python3.10-venv
```

```sh
~~~ sudo rm /usr/bin/python ~~~
sudo rm /usr/bin/python3
sudo ln -s /usr/local/bin/python3.10 /usr/bin/python3
~~~ sudo ln -s /usr/bin/python3 /usr/bin/python ~~~
```


## Update sqlite3 version 2.27.2 to 3.36.0
at least sqlite3 version 3.35.0 needed 
```sh
pi@raspberrypi:~ $ source /var/www/playem/python/env/bin/activate
(env) pi@raspberrypi:~/.playem $ python3
>>> import sqlite3
>>> sqlite3.sqlite_version
'3.27.2'
```

```sh
(env) pi@raspberrypi:~/tmp $ wget https://sqlite.org/2021/sqlite-autoconf-3360000.tar.gz
(env) pi@raspberrypi:~/tmp $ tar -xvf sqlite-autoconf-3360000.tar.gz
(env) pi@raspberrypi:~/tmp $ cd sqlite-autoconf-3360000
(env) pi@raspberrypi:~/tmp/sqlite-autoconf-3360000 $ ./configure
(env) pi@raspberrypi:~/tmp/sqlite-autoconf-3360000 $ make
(env) pi@raspberrypi:~/tmp/sqlite-autoconf-3360000 $ sudo make install
```

unfortunatelly the *make install* command fails with the following:
```sh
make[1]: Leaving directory '/home/pi/tmp/sqlite-autoconf-3360000'
```

Fix it by running the following
```sh
sudo cp /usr/local/lib/*sql* /usr/lib/arm-linux-gnueabihf/
sudo chmod a+x /usr/lib/arm-linux-gnueabihf/*sql*
```

Check the version now
```sh
(env) pi@raspberrypi:~/tmp/sqlite-autoconf-3360000 $ python
Python 3.7.3 (default, Oct 31 2022, 14:04:00) 
[GCC 8.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import sqlite3
>>> sqlite3.sqlite_version
'3.36.0'
```







### Install WSGI module to appache2
```sh
sudo apt-get install libapache2-mod-wsgi-py3 python-dev
sudo a2enmod wsgi 
```

### Clone the project
```sh
mkdir ~/Projects
cd ~/Projects
git clone https://github.com/dallaszkorben/playem.git
sudo ln -s  /home/pi/Projects/playem/var/www/playem/ /var/www/playem
sudo ln -s  /home/pi/Projects/playem/etc/apache2/sites-available/playem.conf /etc/apache2/sites-available/
sudo rm /etc/apache2/sites-enabled/*.conf
sudo ln -s  /etc/apache2/sites-available/playem.conf /etc/apache2/sites-enabled/
```

### Create virtual environment
```sh
sudo rm /usr/lib/python3.11/EXTERNALLY-MANAGED
python3 -m pip install virtualenv
echo "PATH=$PARH:/home/pi/.local/bin" >> /home/pi/.bashrc
cd /home/pi/Projects/playem/var/www/playem/pyton
virtualenv --python=python3 env
```

### Install python packages
```sh
sudo apt-get install python3-distutils

source /home/pi/Projects/playem/var/www/playem/python/env/bin/activate

python -m pip install Flask==2.1.2
python -m pip install Flask-Classful==0.15.0b1
python -m pip install Flask-Cors==3.0.10

python -m pip uninstall Werkzeug
python -m pip install Werkzeug==2.1.2

python -m pip install python-dateutil
python -m pip install distlib
python -m pip install pyyaml

```

### Install extra packages
```sh
sudo apt-get install yp
```

### Mount the media
Mount your playem media folder to the /var/www/playem/MEDIA folder
1. connect the device
2. mount the device:
```sh
$ sudo mount /dev/sda1 /media/pi
```
3. mount the media folder to the MEDIA folder
```sh
$ sudo mount -o bind /home/pi/Projects/python/playem/var/www/playem /var/www/playem
$ sudo mount -o bind  /media/pi/MEDIA /var/www/playem/MEDIA/
```

### Configure Apache
copy the playem/etc/apache2/site-available folder to the /etc/apache2 folder

copy the playem/etc/apache2/envvars file to the /etc/apache2 folder

Why do you need the envvars file?
The critical part is this

```sh
## Uncomment the following line to use the system default locale instead:
. /etc/default/locale
```
If you do not do that, the os.listdir() in the code will fail in case of UTF-8 characters in the file name

Check if the apache configuration is OK
```sh
sudo apachectl configtest
```

Restart the apache
```sh
sudo systemctl restart apache2.service
```

### Automate the mount and Apache start

Create shell script
```sh


sudo touch /usr/local/bin/startplayem.sh
sudo bash -c 'echo -e "#!/bin/bash" >> /usr/local/bin/startplayem.sh'
sudo bash -c 'echo -e "sudo mount -o bind /home/pi/Projects/python/playem/var/www/playem/ /var/www/playem/" >> /usr/local/bin/startplayem.sh'
sudo bash -c 'echo -e "sleep 20" >> /usr/local/bin/startplayem.sh'
sudo bash -c 'echo -e "sudo mount -o bind /media/pi/vegyes/MEDIA /var/www/playem/MEDIA/" >> /usr/local/bin/startplayem.sh'
sudo bash -c 'echo -e "sleep 20" >> /usr/local/bin/startplayem.sh'
sudo bash -c 'echo -e "sudo systemctl restart apache2" >> /usr/local/bin/startplayem.sh'
```

Modify the crontab config file to make the script run after the reboot automatically
```sh
(crontab -l 2>/dev/null; echo "@reboot /usr/local/bin/startplayem.sh  >> /home/pi/.playem/startplayem.log 2>&1") | crontab -
```



### Umount the media
```sh
$ sudo umount /var/www/playem/MEDIA
$ sudo systemctl stop apache2
$ sudo umount /var/www/playem
$ sudo umount /dev/sda1
```



