#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOxServer instance configuration
# Author(s): Martin Paces <martin.paces@eox.at>
#            Daniel Santillan <daniel.santillan@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Copying instance templates ... "


# NOTE: Multiple EOxServer instances are not foreseen in VIRES.

[ -z "$VIRES_SERVER_HOME" ] && error "Missing the required VIRES_SERVER_HOME variable!"
[ -z "$VIRES_USER" ] && error "Missing the required VIRES_USER variable!"


INSTANCE="`basename "$VIRES_SERVER_HOME"`"
INSTROOT="`dirname "$VIRES_SERVER_HOME"`"

TEMPLATES_SRC="/usr/local/vires-dempo_ops/templates"
TEMPLATES="${INSTROOT}/${INSTANCE}/${INSTANCE}/templates"

#-------------------------------------------------------------------------------
# STEP 1: COPY INSTANCE SPECIFIC TEMPLATES
sudo -u "$VIRES_USER" cp -r "$TEMPLATES_SRC/." "$TEMPLATES"


