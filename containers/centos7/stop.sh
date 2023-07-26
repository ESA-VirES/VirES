#!/bin/sh
#
# Stop detached named container
#

[ -z "$1" ] && {
    echo "USAGE `basename $0` <image>" >&2
    exit 1
} 2>&1

DIR="$(cd "$(dirname $0)" ; pwd )"
. $DIR/common.sh
. $DIR/$1/common.sh

if [ -z "$CONTAINER_NAME" ]
then
    echo "Container name is not configured." >&2
    exit 1
fi

if ! $CT_COMMAND container exists "$CONTAINER_NAME"
then
    echo "Container $CONTAINER_NAME does not exist." >&2
    exit 0
fi

CONTANER_ID=`$CT_COMMAND ps --format={{.ID}}  --filter "name=$CONTAINER_NAME"`
if [ -z "$CONTANER_ID" ]
then
    echo "Container $CONTAINER_NAME is not running." >&2
    exit 0
fi

echo "Stopping $CONTAINER_NAME container ..." >&2
$CT_COMMAND container stop "$CONTAINER_NAME"
