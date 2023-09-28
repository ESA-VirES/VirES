#!/usr/bin/bash

# Clean-up the /run/httpd directory removing any stuff from the previous run
# which might prevent successful start of the httpd daemon.
find /run/httpd -type f -exec rm -fv {} \;

if [ -z "$*" ]
then
    exec httpd -D FOREGROUND
else
    exec "$@"
fi
