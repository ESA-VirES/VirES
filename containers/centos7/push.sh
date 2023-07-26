#!/bin/sh
#
# push image to registry
#

[ -z "$1" ] && {
    echo "USAGE `basename $0` <image>"
    exit 1
} 2>&1

DIR=`dirname $0`
. $DIR/common.sh
. $DIR/$1/common.sh

set -x
$CT_COMMAND push "$IMAGE"
