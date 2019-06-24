#!/bin/sh
#
# Django manage.py convenience wrapper. 
#

[ -f "`dirname $0`/user.conf" ] && . `dirname $0`/user.conf
. `dirname $0`/lib_common.sh

if [ "$1" == '-u' ]
then
    USER="$2"
    shift 2
else
    USER="$VIRES_USER"
fi

[ -z "$USER" ] && { echo "ERROR: No user given!" >&2 ; exit 2 ; }

sudo -u "$USER" `dirname $0`/virtualenv_execute.sh python "$VIRES_SERVER_HOME/manage.py" "$@"
