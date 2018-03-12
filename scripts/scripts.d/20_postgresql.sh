#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: PostgreSQL and PostGIS installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing PosgreSQL RDBMS ... "

PG_DATA_DIR_DEFAULT="/var/lib/pgsql/data"
PG_DATA_DIR="${VIRES_PGDATA_DIR:-$PG_DATA_DIR_DEFAULT}"

# Install RPM packages
yum --assumeyes install postgresql postgresql-server postgis

# Shut-down the postgress if already installed and running.
if [ -n "`systemctl | grep postgresql.service`" ]
then
    info "Stopping running PostgreSQL server ..."
    systemctl stop postgresql.service
fi

# Check if the database location changed since the last run.
CONF_FILE="$HOME/.pg_data_dir"
[ -f "$CONF_FILE" ] && PG_DATA_DIR_LAST="`head -n 1 "$CONF_FILE"`"

if [ "$PG_DATA_DIR" == "$PG_DATA_DIR_LAST" ]
then
    info "PostgreSQL data location already set to $PG_DATA_DIR"

    systemctl start postgresql.service
    systemctl status postgresql.service
    exit 0
fi

info "Removing the existing PosgreSQL DB cluster ..."
rm -fR "$PG_DATA_DIR_DEFAULT"
rm -fR "$PG_DATA_DIR"
rm -fR "$PG_DATA_DIR_LAST"
rm -f "`dirname $0`/../db.conf"

info "Setting the PostgreSQL data location to: $PG_DATA_DIR"
cat >/etc/systemd/system/postgresql.service <<END
.include /lib/systemd/system/postgresql.service
[Service]
Environment=PGDATA=$PG_DATA_DIR
END
systemctl daemon-reload

info "New database initialisation ... "
postgresql-setup initdb
systemctl disable postgresql.service # DO NOT REMOVE!
systemctl enable postgresql.service
systemctl start postgresql.service
systemctl status postgresql.service

# Setup postgis database template.
if [ -z "`sudo -u postgres psql --list | grep template_postgis`" ]
then
    sudo -u postgres createdb template_postgis
    #sudo -u postgres createlang plpgsql template_postgis

    PG_SHARE=/usr/share/pgsql
    POSTGIS_SQL="postgis-64.sql"
    [ -f "$PG_SHARE/contrib/$POSTGIS_SQL" ] || POSTGIS_SQL="postgis.sql"
    sudo -u postgres psql -q -d template_postgis -f "$PG_SHARE/contrib/$POSTGIS_SQL"
    sudo -u postgres psql -q -d template_postgis -f "$PG_SHARE/contrib/spatial_ref_sys.sql"
    sudo -u postgres psql -q -d template_postgis -c "GRANT ALL ON geometry_columns TO PUBLIC;"
    sudo -u postgres psql -q -d template_postgis -c "GRANT ALL ON geography_columns TO PUBLIC;"
    sudo -u postgres psql -q -d template_postgis -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"
fi

# Store current data location.
echo "$PG_DATA_DIR" > "$CONF_FILE"
