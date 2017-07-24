#Install Python 3

cd ~
wget https://www.python.org/ftp/python/3.5.1/Python-3.5.1.tgz
tar -zxvf Python-3.5.1.tgz
cd Python-3.5.1
./configure && make && sudo make install

#Get packages from apt.sh
apt-get install python-scapy blueZ pkg-config libboost-python-dev libboost-thread-dev libbluetooth-dev >= 4.101 libglib2.0-dev python-dev 
sudo apt-get install python-pip python-dev ipython

# install requirements.txt