#-------------------------------------------------------------------------------
#
# Purpose: EOxServer instance configuration - development customisation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_apache.sh

info "Configuring EOxServer instance (developepment mods)... "

# NOTE: Multiple EOxServer instances are not foreseen in VIRES.

[ -z "$VIRES_SERVER_HOME" ] && error "Missing the required VIRES_SERVER_HOME variable!"
[ -z "$VIRES_USER" ] && error "Missing the required VIRES_USER variable!"

INSTANCE="`basename "$VIRES_SERVER_HOME"`"
INSTROOT="`dirname "$VIRES_SERVER_HOME"`"

SETTINGS="${INSTROOT}/${INSTANCE}/${INSTANCE}/settings.py"

#-------------------------------------------------------------------------------
# EOXSERVER CONFIGURATION

sudo -u "$VIRES_USER" ex "$SETTINGS" <<END
g/^DEBUG\s*=/s#\(^DEBUG\s*=\s*\).*#\1True#
.
wq
END

#-------------------------------------------------------------------------------
# FINAL WEB SERVER RESTART
sudo systemctl restart httpd.service
sudo systemctl status httpd.service
