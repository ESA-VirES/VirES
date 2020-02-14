#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Remove existing EOxServer instance.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

# NOTE: To drop the existing database remove the db.conf file in the scritps directory.

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_eoxserver.sh

set_instance_variables

required_variables INSTROOT INSTANCE EOXSLOG ACCESSLOG
required_variables VIRES_WPS_TEMP_DIR VIRES_WPS_PERM_DIR VIRES_WPS_TASK_DIR

if [ -d "$INSTROOT/$INSTANCE" ]
then
    info "Removing EOxServer instance ..."
    rm -fR "$INSTROOT/$INSTANCE"

    # remove logfiles
    [ ! -f "$EOXSLOG" ] || rm -f "$EOXSLOG"
    [ ! -f "$ACCESSLOG" ] || rm -f "$ACCESSLOG"

    # remove WPS directories
    [ -d "$VIRES_WPS_TEMP_DIR" ] && rm -fR "$VIRES_WPS_TEMP_DIR"
    [ -d "$VIRES_WPS_PERM_DIR" ] && rm -fR "$VIRES_WPS_PERM_DIR"
    [ -d "$VIRES_WPS_TASK_DIR" ] && rm -fR "$VIRES_WPS_TASK_DIR"

    info "EOxServer instance was removed."
else
    info "EOxServer instance does not exist."
fi
