#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Remove existing VirES-Server instance.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

# NOTE: To drop the existing database remove the db.conf file in the scritps directory.

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_vires.sh

set_instance_variables

required_variables INSTROOT INSTANCE VIRESLOG ACCESSLOG
required_variables VIRES_WPS_TEMP_DIR VIRES_WPS_PERM_DIR VIRES_WPS_TASK_DIR

if [ -d "$INSTROOT/$INSTANCE" ]
then
    info "Removing VirES-Server instance ..."
    rm -fR "$INSTROOT/$INSTANCE"

    # remove logfiles
    [ ! -f "$VIRESLOG" ] || rm -f "$VIRESLOG"
    [ ! -f "$ACCESSLOG" ] || rm -f "$ACCESSLOG"

    # remove WPS directories
    [ -d "$VIRES_WPS_TEMP_DIR" ] && rm -fR "$VIRES_WPS_TEMP_DIR"
    [ -d "$VIRES_WPS_PERM_DIR" ] && rm -fR "$VIRES_WPS_PERM_DIR"
    [ -d "$VIRES_WPS_TASK_DIR" ] && rm -fR "$VIRES_WPS_TASK_DIR"

    info "VirES-Server instance was removed."
else
    info "VirES-Server instance does not exist."
fi
