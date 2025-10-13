#!/usr/bin/bash
#
# pg_ctl -D /var/lib/postgresql/data - logfile start
# 
export PGDATA=/var/lib/postgresql/data

if [ ! -s "$PGDATA/PG_VERSION" ]
then
    # database has not been initialized yet
    initdb --encoding=UTF8
fi

if [ -z "$*" ]
then
    echo "Starting posgres server ... "
    echo "Logs are collected to $LOG_DIR/postgresql.log log file."
    exec postgres 2>&1 | tee "$LOG_DIR/postgresql.log"
else
    exec "$@"
fi
