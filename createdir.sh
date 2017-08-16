#!/bin/bash

USERNAME="$1"

# Check if username already exists
while true; do
    id "$USERNAME"
    if [ $? -eq 0 ]; then
        break
    fi
    echo "Username doesn't exist. Sleeping for 60s..."
    sleep 60s
done

BASEDIR="/mnt/ftp_pool/FTP/Others"

# Create dir
USERDIR="$BASEDIR/$USERNAME"
sudo mkdir -p "$USERDIR/DL/DAD/manual_requests"
sudo mkdir -p "$USERDIR/DL/DAD/lipad_requests"

# Link FAQ.txt
cd "$USERDIR"
ln -sf ../FAQ.txt ./

# Set acls
/mnt/misc/scripts/sysad-tools/set-acls/set_acls.py "$USERDIR"
