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


### Install WSGI module to appache2
```sh
sudo apt-get install libapache2-mod-wsgi-py3 python-dev
sudo a2enmod wsgi 
```

### Clone the project
```sh
mkdir ~/Projects
cd ~/Projects
git clone https://github.com/dallaszkorben/diy-greenwall.git
sudo ln -s  /home/pi/Projects/playem/var/www/playem/ /var/www/playem
sudo ln -s  /home/pi/Projects/playem/etc/apache2/sites-available/playem.conf /etc/apache2/sites-available/
sudo rm /etc/apache2/sites-enabled/*.conf
sudo ln -s  /etc/apache2/sites-available/playem.conf /etc/apache2/sites-enabled/
```

### Create file system for your code - Before the project was pushed first time - Skip it
```sh
python3 -m pip install virtualenv
cd /var/www/playem
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





