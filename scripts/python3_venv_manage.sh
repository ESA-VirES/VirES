#!/bin/sh
#
# Django manage.py convenience wrapper. 
#

[ -f "`dirname $0`/user.conf" ] && . `dirname $0`/user.conf
. `dirname $0`/lib_common.sh

sudo -u "$VIRES_USER" `dirname $0`/python3_venv_execute.sh python "$OAUTH_SERVER_HOME/manage.py" "$@"
