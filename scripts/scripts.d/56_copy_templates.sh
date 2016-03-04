#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Load fixtures to the EOxServer instance.
# Author(s): Martin Paces <martin.paces@eox.at>
#            Daniel Santillan <daniel.santillan@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH


. `dirname $0`/../lib_logging.sh

info "Copy available templates ... "

[ -z "$VIRES_SERVER_HOME" ] && error "Missing the required VIRES_SERVER_HOME variable!"
[ -z "$VIRES_USER" ] && error "Missing the required VIRES_USER variable!"


INSTANCE="`basename "$VIRES_SERVER_HOME"`"
INSTROOT="`dirname "$VIRES_SERVER_HOME"`"
VAGRANT_SRC="/usr/local/vires-dempo_ops/templates"
TEMPLATES_DIR_SRC="${TEMPLATES_DIR_SRC:-$VAGRANT_SRC}"
TEMPLATES_DIR_DST="${INSTROOT}/${INSTANCE}/${INSTANCE}/templates"


sudo -u "$VIRES_USER" cp -r "$TEMPLATES_DIR_SRC/." "$TEMPLATES_DIR_DST"