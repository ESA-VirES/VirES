#!/bin/bash
#
# Simple script dropping PosgreSQL database role

[ -z "$1" ] && {
    echo "USAGE `basename $0` <db-user>"
    exit 1
} 2>&1

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

remove_db_user() {
    # check if the user already exists
    TMP=`psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DBUSER' ;"`
    if [ 1 == "$TMP" ]
    then
        psql -q -c "DROP USER $DBUSER ;" \
            && info "The existing user '$DBUSER' user was removed." \
            || error "Failed to remove the existing user '$DBUSER'." 
    else
        warn "The database user '$DBUSER' does not exist."
    fi
}

DBUSER="$1"

remove_db_user
