#!/bin/bash
# Ghost Hunter for Pi startup script
# Version 0.1
# Elliott Hall
GHOSTHUNT_DIR="/home/pi/projects/ghosthunt"

# Need to be root to have access to bluetooth
sudo su root
source $GHOSTHUNT_DIR/ghosthunter/envs/ghosthunter/bin/activate
cd $GHOSTHUNT_DIR
# git pull

# pip update

# run main script