#!/bin/sh
#
# Show logs of a named container
#
[ -z "$1" ] && {
    echo "USAGE `basename $0` <image> [<options>]"
    exit 1
} 2>&1

DIR="$(cd "$(dirname $0)" ; pwd )"
. $DIR/common.sh
. $DIR/$1/common.sh

shift

if [ -z "$CONTAINER_NAME" ]
then
    echo "Not a named container."
    exit 1
fi

exec $CT_COMMAND logs $@ "$CONTAINER_NAME"
