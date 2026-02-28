#!/usr/bin/bash
#

if [ -z "$*" ]
then
    echo "Starting redis server ... "
    exec redis-server /etc/redis/redis.conf --daemonize no
else
    exec "$@"
fi
