#!/bin/bash

USERNAME="$1"
BASEDIR="/mnt/backup_pool/geostorage/FTP/Others"
BASEUSER="datamanager"
BASEGROUP="data-managrs"
DEFAULTACLS="/mnt/backup_pool/scripts/set_acls/lipad_default_acls"
USERACLS="user:${USERNAME}:r-x---a-R-c---:fd----:allow"

# Create dir
USERDIR="$BASEDIR/$USERNAME"
mkdir -p $USERDIR

#chown $BASEUSER:$BASEGROUP $USERDIR

# Set acls
setfacl -M $DEFAULTACLS $USERDIR
setfacl -m $USERACLS $USERDIR
