#!/bin/bash
# Ghost Hunter for Pi startup script
# Version 0.1
# Elliott Hall
GHOSTHUNT_DIR="/home/pi/projects/ghosthunt"

# Update sources
cd "$GHOSTHUNT_DIR/ghosthunter"
# git pull

# pip update

# Need to be root to have access to bluetooth
sudo su root
source "$GHOSTHUNT_DIR/envs/ghosthunter/bin/activate"


# run main script