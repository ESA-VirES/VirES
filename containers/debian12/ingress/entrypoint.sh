#!/usr/bin/bash

mkdir_and_chown() {
    [ -d "$2" ] || { mkdir -p "$2" ; chown "$1" "$2"; }
}

# get Apache configuration
APACHE_CONFDIR="/etc/apache2"
. "$APACHE_CONFDIR/envvars"

mkdir_and_chown "root:root" "$APACHE_RUN_DIR"
mkdir_and_chown "$APACHE_RUN_USER:$APACHE_RUN_GROUP" "$APACHE_RUN_DIR/socks"
mkdir_and_chown "$APACHE_RUN_USER:$APACHE_RUN_GROUP" "$APACHE_LOCK_DIR"

# Clean-up the run directory removing any stuff from the previous run
# which might prevent successful start of the Apache daemon.
find "$APACHE_RUN_DIR" -type f -exec rm -fv {} \;

if [ -z "$*" ]
then
    exec apache2 -D FOREGROUND
else
    exec "$@"
fi
