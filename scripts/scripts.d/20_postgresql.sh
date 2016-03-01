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
#======================================================================

# STEP 1: INSTALL RPM PACKAGES
yum --assumeyes install postgresql postgresql-server postgis python-psycopg2

# STEP 2: Shut-down the postgress if already installed and running.
if [ -n "`systemctl | grep postgresql.service`" ]
then
    info "Stopping running PostgreSQL server ..."
    systemctl stop postgresql.service
fi

# STEP 3: CONFIGURE THE STORAGE DIRECTORY
info "Removing the existing PosgreSQL DB cluster ..."
[ ! -d "$PG_DATA_DIR_DEFAULT" ] || rm -fR "$PG_DATA_DIR_DEFAULT"
[ ! -d "$PG_DATA_DIR" ] || rm -fR "$PG_DATA_DIR"

info "Setting the PostgreSQL data location to: $PG_DATA_DIR"
cat >/etc/systemd/system/postgresql.service <<END
.include /lib/systemd/system/postgresql.service
[Service]
Environment=PGDATA=$PG_DATA_DIR
END
systemctl daemon-reload

# STEP 4: INIT THE DB AND START THE SERVICE
info "New database initialisation ... "

postgresql-setup initdb
systemctl disable postgresql.service # DO NOT REMOVE!
systemctl enable postgresql.service
systemctl start postgresql.service
systemctl status postgresql.service

# STEP 5: SETUP POSTGIS DATABASE TEMPLATE
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
