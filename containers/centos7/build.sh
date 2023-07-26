#!/bin/sh
#
# container build scrips
#

[ -z "$1" ] && {
    echo "USAGE `basename $0` <image>"
    exit 1
} 2>&1

DIR="$(cd "$(dirname $0)" ; pwd )"
. $DIR/common.sh
. $DIR/$1/common.sh

{
    set -x
    cd $DIR/$1
    $CT_COMMAND build $BUILD_OPTIONS -t "$IMAGE" .
} 2>&1 | tee "$DIR/$1/build.log"
