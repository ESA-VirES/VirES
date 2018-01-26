#-------------------------------------------------------------------------------
#
# Purpose: EOxServer instance configuration - development customisation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Configuring EOxServer instance (developepment mods)... "

[ -z "$VIRES_SERVER_HOME" ] && error "Missing the required VIRES_SERVER_HOME variable!"

INSTANCE="`basename "$VIRES_SERVER_HOME"`"
INSTROOT="`dirname "$VIRES_SERVER_HOME"`"

SETTINGS="${INSTROOT}/${INSTANCE}/${INSTANCE}/settings.py"

#-------------------------------------------------------------------------------
# EOXSERVER CONFIGURATION

info "Enabling debuging mode ..."

ex "$SETTINGS" <<END
g/^DEBUG\s*=/s#\(^DEBUG\s*=\s*\).*#\1True#
.
wq
END

#-------------------------------------------------------------------------------
# FINAL WEB SERVER RESTART
#systemctl restart httpd.service
#systemctl status httpd.service
