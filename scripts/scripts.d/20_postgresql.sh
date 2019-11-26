#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: PostgreSQL and PostGIS installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_postgres.sh

CONF_FILE="$HOME/.pg_data_dir"

info "Installing PosgreSQL RDBMS ... "

PG_DATA_DIR="${VIRES_PGDATA_DIR:-$PG_DATA_DIR_DEFAULT}"

if [ -n "`systemctl | grep $PG_SERVICE_NAME`" ]
then
    info "Stopping running PostgreSQL server ..."
    PG_DATA_DIR_LAST=`sudo -u postgres psql -qA -c 'SHOW data_directory;' | grep -m 1 '^/'`
    systemctl stop $PG_SERVICE_NAME
else
    [ -f "$CONF_FILE" ] && PG_DATA_DIR_LAST="`head -n 1 "$CONF_FILE"`"
fi

# Install RPM packages
yum --assumeyes install postgresql96 postgresql96-server
yum --assumeyes --setopt=obsoletes=0 install postgis2_96

# Check if the database location changed since the last run.
[ -f "$CONF_FILE" -a -z "$PG_DATA_DIR_LAST" ] && PG_DATA_DIR_LAST="`head -n 1 "$CONF_FILE"`"

# set RESET_DB variable to YES to remove the existing database
if [ "$PG_DATA_DIR" == "$PG_DATA_DIR_LAST" -a -z "$RESET_DB" ]
then
    info "PostgreSQL data location already set to $PG_DATA_DIR"
    info "Preserving the existing PosgreSQL DB cluster ..."

    systemctl start $PG_SERVICE_NAME
    systemctl status $PG_SERVICE_NAME
    exit 0
fi

info "Removing the existing PosgreSQL DB cluster ..."
rm -fR "$PG_DATA_DIR_DEFAULT"
rm -fR "$PG_DATA_DIR"
rm -fR "$PG_DATA_DIR_LAST"
rm -fv "`dirname $0`/../"db_*.conf

info "Setting the PostgreSQL data location to: $PG_DATA_DIR"
cat >/etc/systemd/system/$PG_SERVICE_NAME <<END
.include /lib/systemd/system/$PG_SERVICE_NAME
[Service]
Environment=PGDATA=$PG_DATA_DIR
END

systemctl daemon-reload

info "New database initialisation ... "

postgresql-setup initdb

# Store current data location.
echo "$PG_DATA_DIR" > "$CONF_FILE"

systemctl disable $PG_SERVICE_NAME # DO NOT REMOVE!
systemctl enable $PG_SERVICE_NAME
systemctl start $PG_SERVICE_NAME
systemctl status $PG_SERVICE_NAME
