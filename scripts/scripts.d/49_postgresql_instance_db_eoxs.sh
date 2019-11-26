#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: PostgreSQL instance database creation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

# NOTE: To drop the existing database remove the db.conf file in the scritps directory.

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_postgres.sh
. `dirname $0`/../lib_eoxserver.sh

DB_CONF="`dirname $0`/../db_eoxs.conf"

info "Creating EOxServer instance's Postgres database ..."

# check if the database is already configured and if so skip the creation ...
load_db_conf "$DB_CONF"

if [ -n "$DBENGINE" -a "$DBNAME" ]
then
    info "Reusing configured existing database $DBNAME ($DBENGINE) rather then creating a new one."
    exit 0
fi

# set and save new database configuration ...
set_instance_variables

DBENGINE="django.contrib.gis.db.backends.postgis"
DBNAME="eoxs_${INSTANCE}"
DBUSER="eoxs_admin_${INSTANCE}"
DBPASSWD="${INSTANCE}_admin_eoxs_`head -c 24 < /dev/urandom | base64 | tr '/' '_'`"
DBHOST=""
DBPORT=""

save_db_conf "$DB_CONF"

# deleting any previously existing database
sudo -u postgres psql -q -c "DROP DATABASE $DBNAME ;" 2>/dev/null \
  && warn " The already existing database '$DBNAME' was removed." || /bin/true

# deleting any previously existing user
TMP=`sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DBUSER' ;"`
if [ 1 == "$TMP" ]
then
    sudo -u postgres psql -q -c "DROP USER $DBUSER ;"
    warn " The alredy existing database user '$DBUSER' was removed"
fi

# create new users
sudo -u postgres psql -q -c "CREATE USER $DBUSER WITH ENCRYPTED PASSWORD '$DBPASSWD' NOSUPERUSER NOCREATEDB NOCREATEROLE ;"
sudo -u postgres psql -q -c "CREATE DATABASE $DBNAME WITH OWNER $DBUSER ENCODING 'UTF-8' ;"
sudo -u postgres psql -q -d "$DBNAME" -c "CREATE EXTENSION IF NOT EXISTS postgis ;"

# prepend to the beginning of the acess list
PG_HBA="`sudo -u postgres psql -qA -c "SHOW hba_file;" | grep -m 1 "^/"`"
{ sudo -u postgres ex "$PG_HBA" || /bin/true ; } <<END
g/# EOxServer instance:.*\/$INSTANCE/d
g/^\s*local\s*$DBNAME/d
/#\s*TYPE\s*DATABASE\s*USER\s*.*ADDRESS\s*METHOD/a
# EOxServer instance: $INSTROOT/$INSTANCE
local	$DBNAME	$DBUSER	md5
local	$DBNAME	all	reject
.
wq
END

systemctl restart $PG_SERVICE_NAME
systemctl status $PG_SERVICE_NAME
