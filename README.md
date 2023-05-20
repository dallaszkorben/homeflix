# playem
web media player


## Prepare Raspberry Pi 4 


### Get rid of the old python 
```sh
sudo apt-get update
sudo apt-get upgrade

sudo apt -s remove python2.7
sudo apt -s remove python2
sudo apt-get autoremove
```

### Install WSGI module to appache2
```sh
sudo apt-get install libapache2-mod-wsgi-py3 python-dev
python -m pip install mod-wsgi
sudo a2enmod wsgi 


(==>
sudo mkdir /usr/local/programs
sudo chown root:pi /usr/local/programs
sudo chmod 775 /usr/local/programs
cd /usr/local/programs

wget https://www.python.org/ftp/python/3.9.15/Python-3.9.15.tgz
tar -zxvf Python-3.9.15.tgz
cd /usr/local/programs/Python-3.9.15
./configure --enable-optimizations
sudo make altinstall
sudo rm /usr/bin/python
sudo rm /usr/bin/python3
sudo ln -s /usr/local/bin/python3.9 /usr/bin/python
sudo ln -s /usr/local/bin/python3.9 /usr/bin/python3
python -m pip --version
python -m pip install --upgrade pip
<==)


### Create file system for your code - Before the project was pushed first time - Skip it
```sh
python3 -m pip install virtualenv
sudo ln -s  /home/pi/Projects/playem/var/www/playem/ /var/www/playem
cd /var/www/playem
virtualenv --python=python3 env
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

### Install python packages
```sh
source /home/pi/Projects/playem/var/www/playem/python/env/bin/activate
python -m pip install Flask==2.1.2
python -m pip install Flask-Classful==0.15.0b1
python -m pip install Flask-Cors==3.0.10
python -m pip install python-dateutil
```
