#!/bin/bash
#
# generate new random credentials
#
#
[ -z "$1" -o -z "$2" ] && {
    echo "USAGE `basename $0` <db-name> <db-user> "
    exit 1
} 2>&1

echo DBNAME="$1"
echo DBUSER="$2"
echo DBPASSWD="`head -c 24 < /dev/urandom | base64 | tr '/' '_'`"
shift 2
echo DBEXTENSIONS="$*"
