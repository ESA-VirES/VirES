#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Initial IPTables firewall configuration.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Starting the firewall ... "

[ "$ENABLE_FIREWALL" = "YES" ] || {
    info "Firewall start skipped."
    exit 0
}

# Start the firewall daemon using the default firewall zone enabled services.
systemctl enable firewalld
systemctl start firewalld.service
systemctl status firewalld.service
