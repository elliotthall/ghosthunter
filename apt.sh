

#Installing Python 3.5 on Pi
#https://raspberrypi.stackexchange.com/questions/54365/how-to-download-and-install-python-3-5-in-raspbian/56632#56632

#Get packages from apt.sh
sudo apt-get install python-dev python-scapy blueZ libglib2.0-dev
# May not be needed pkg-config libboost-python-dev libboost-thread-dev libbluetooth-dev >= 4.101
sudo apt-get install python-pip python-dev ipython python3-pip

# install requirements.txt