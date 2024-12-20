#!/bin/bash
#
# Simple script creating PosgreSQL database from the configuration passed
# via standard input.
#
#  create_db.sh <<END
#  DBNAME=mydatabase
#  DBUSER=db_admin
#  DBPASSWD=my_password
#  DBEXTENSIONS=postgis  # comma separated list
#  END

info() {
  echo "INFO: $*" >&2
}

warn() {
  echo "WARNING: $*" >&2
}

error() {
  echo "ERROR: $*" >&2
  exit 1
}

clear_variables() {
    # clear listed variables
    for __VARIABLE___
    do
        unset "${__VARIABLE___}"
    done
}


check_required_variables() {
    # check existence of the listed variables
    for __VARIABLE___
    do
        if [ -z "${!__VARIABLE___}" ]
        then
             error "ERROR: Missing required ${__VARIABLE___} value!"
        fi
    done
}

remove_existing_db() {
    # deleting an existing database
    TMP=`psql -tAc "SELECT 1 FROM pg_database WHERE datname = '$DBNAME' ;"`
    if [ 1 == "$TMP" ]
    then
      warn "The '$DBNAME' database already exists." \
      # terminate connections before dropping the database
      psql -q -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DBNAME' ;" >/dev/null \
        && psql -q -c "DROP DATABASE $DBNAME ;" \
        && info "The existing database '$DBNAME' was removed." >&2 \
        || error "Failed to remove the existing database '$DBNAME'."
    fi
}

stop_if_db_exists() {
    TMP=`psql -tAc "SELECT 1 FROM pg_database WHERE datname = '$DBNAME' ;"`
    if [ 1 == "$TMP" ]
    then
      info "The '$DBNAME' database already exists."
      exit 0
    fi
}

create_new_db() {
    # create database
    psql -q -c "CREATE DATABASE $DBNAME WITH OWNER $DBUSER ENCODING 'UTF-8' ;" \
      && info "The database '$DBNAME' owned by '$DBUSER' was created."

    # create extensions
    if [ -n "$DBEXTENSIONS" ]
    then
        echo "$DBEXTENSIONS" | tr ',' '\n' | while read DBEXTENSION
        do
            psql -q -d "$DBNAME" -c "CREATE EXTENSION IF NOT EXISTS $DBEXTENSION ;" \
                && info "The '$DBEXTENSION' extension of the '$DBNAME' database was created." \
                || error "Failed to create '$DBEXTENSION' extension of the '$DBNAME' database."
        done
    fi
}

restrict_db_access() {
    # make the DB accessible for the dedicated user only
    PG_HBA="$PGDATA/pg_hba.conf"
    { ed -vs "$PG_HBA" || /bin/true ; } <<END
g/^\s*local\s*$DBNAME/d
g/^\s*host\s*$DBNAME/d
/#\s*TYPE\s*DATABASE\s*USER\s*.*ADDRESS\s*METHOD/a
host    $DBNAME $DBUSER 127.0.0.1/32 md5
host    $DBNAME $DBUSER ::1/128 md5
local   $DBNAME $DBUSER md5
host    $DBNAME all 127.0.0.1/32 reject
host    $DBNAME all ::1/128 reject
local   $DBNAME all reject
.
wq
END
    psql -q -c "SELECT pg_reload_conf();" >/dev/null

}


clear_db_access() {
    # remove any DB-specific access restrictions
    PG_HBA="$PGDATA/pg_hba.conf"
    { ed -vs "$PG_HBA" || /bin/true ; } <<END
g/^\s*local\s*$DBNAME/d
g/^\s*host\s*$DBNAME/d
wq
END
    psql -q -c "SELECT pg_reload_conf();" >/dev/null
}


create_update_db_user() {
    # check if the user already exists
    TMP=`psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DBUSER' ;"`
    if [ 1 == "$TMP" ]
    then
        warn "The database user '$DBUSER' already exists."
        # user exists
        psql -q -c "ALTER USER $DBUSER WITH ENCRYPTED PASSWORD '$DBPASSWD' NOSUPERUSER NOCREATEDB NOCREATEROLE ;" \
            && info "The existing user '$DBUSER' user was altered." \
            || error "Failed to alter the existing user '$DBUSER'."
    else
        psql -q -c "CREATE USER $DBUSER WITH ENCRYPTED PASSWORD '$DBPASSWD' NOSUPERUSER NOCREATEDB NOCREATEROLE ;" \
            && info "The user '$DBUSER' was created." \
            || error "Failed to create the user '$DBUSER'."
    fi
}

# Read and parse DB parameters from the standard input ...

clear_variables DBNAME DBUSER DBPASSWD DBEXTENSIONS

# set Internal Field Separator
IFS_OLD="$IFS"
IFS="="
while read KEY VALUE
do
    KEY="`echo "$KEY" | sed -e 's/^\s\+//' -e 's/\s\+$//'`"
    VALUE="`echo "$VALUE" | sed -e 's/^\s\+//' -e 's/\s\+$//'`"
    case "$KEY" in
        DBNAME) DBNAME="$VALUE" ;;
        DBUSER) DBUSER="$VALUE" ;;
        DBPASSWD) DBPASSWD="$VALUE" ;;
        DBEXTENSIONS)
            VALUE="`echo "$VALUE" | sed -e 's/\s*,\s*/,/g'`"
            DBEXTENSIONS="$VALUE" ;;
    esac
done
IFS="$IFS_OLD"

check_required_variables PGDATA DBNAME DBUSER DBPASSWD

if [ "$1" == "--force" ]
then
    remove_existing_db
else
    stop_if_db_exists
fi

clear_db_access
create_update_db_user
create_new_db
restrict_db_access
