#!/usr/bin/bash
#

if [ -z "$*" ]
then
    echo "Starting redis server ... "
    echo "Logs are collected to $LOG_DIR/redis.log log file."
    exec redis-server 2>&1 | tee "$LOG_DIR/redis.log"
else
    exec "$@"
fi
