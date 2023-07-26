#!/bin/sh
#
# Reload (stop, remove, create, start) container
#

[ -z "$1" ] && {
    echo "USAGE `basename $0` <image>" >&2
    exit 1
} 2>&1

DIR="$(cd "$(dirname $0)" ; pwd )"

$DIR/remove.sh "$1"
$DIR/start.sh "$1"
