#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Resource limits configuration.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

#NOTE: So far it works on Centos 7. It's not sure though how long before
#      it gets taken over by systmed.

. `dirname $0`/../lib_logging.sh

info "Setting the resource limits ... "

[ -z "$VIRES_USER" ] && error "Missing the required VIRES_USER variable!"

LIMITS_FILE="/etc/security/limits.d/80-vires-nofile.conf"
info "Setting the limits on number of open files."
info "Limits stored in: $LIMITS_FILE"
cat >"$LIMITS_FILE" <<END
# Default limit for number of open files

*          soft    nofile     2048
*          hard    nofile     2048
$VIRES_USER      soft    nofile     500000
$VIRES_USER      hard    nofile     500000
root       soft    nofile     500000
root       hard    nofile     500000
END
