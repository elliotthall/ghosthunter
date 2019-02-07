#!/bin/bash

echo "Update Ghost Hunter from Git..."
echo -e "GET http://google.com HTTP/1.0\n\n" | nc google.com 80 > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "Online. Updating"
    cd /home/pi/ghosthunt/ghosthunter
    sudo su -c "git pull" pi
else
    echo "Offline"
fi