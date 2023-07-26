#!/bin/sh
#
# pull image from registry
#

[ -z "$1" ] && {
    echo "USAGE `basename $0` <image>"
    exit 1
} 2>&1

DIR="$(cd "$(dirname $0)" ; pwd )"
. $DIR/common.sh
. $DIR/$1/common.sh

set -x
$CT_COMMAND pull "$IMAGE"
