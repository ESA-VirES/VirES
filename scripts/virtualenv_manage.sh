#!/bin/sh
#
# Django manage.py convenience wrapper. 
#

[ -f "`dirname $0`/user.conf" ] && . `dirname $0`/user.conf
. `dirname $0`/lib_common.sh

sudo -u "$VIRES_USER" `dirname $0`/virtualenv_execute.sh python "$VIRES_SERVER_HOME/manage.py" "$@"
