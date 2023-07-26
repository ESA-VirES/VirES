#!/bin/sh
#
# Execute command in a container
#

[ -z "$1" ] && {
    echo "USAGE `basename $0` <image> [<command>]"
    exit 1
} 2>&1

DIR="$(cd "$(dirname $0)" ; pwd )"
. $DIR/common.sh
. $DIR/$1/common.sh

shift

case "$1" in
    -i) TI_OPTIONS="-i" ; shift ;;
    --) TI_OPTIONS="" ; shift ;;
    *) TI_OPTIONS="-ti" ;;
esac

if [ -n "$CONTAINER_NAME" ]
then
    # check if the named container is running and if so
    # execute the command
    CONTANER_ID=`$CT_COMMAND ps --format={{.ID}}  --filter "name=$CONTAINER_NAME"`
    if [ -n "$CONTANER_ID" ]
    then
        set -x
        exec $CT_COMMAND exec $TI_OPTIONS $EXEC_OPTIONS "$CONTAINER_NAME" "${@:-/bin/bash}"
    else
        echo "Container $CONTAINER_NAME is not started."
        exit 1
    fi
fi

set -x
exec $CT_COMMAND run $TI_OPTIONS --rm $RUN_OPTIONS $IMAGE "$@"
