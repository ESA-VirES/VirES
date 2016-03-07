#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Copy templates to the EOxServer instance.
# Author(s): Martin Paces <martin.paces@eox.at>
#            Daniel Santillan <daniel.santillan@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH


. `dirname $0`/../lib_logging.sh

info "Copy available templates ... "

[ -z "$CONTRIB_DIR" ] && error "Missing the required CONTRIB_DIR variable!"
[ -z "$VIRES_SERVER_HOME" ] && error "Missing the required VIRES_SERVER_HOME variable!"
[ -z "$VIRES_USER" ] && error "Missing the required VIRES_USER variable!"
[ -z "$VIRES_GROUP" ] && error "Missing the required VIRES_GROUP variable!"

INSTANCE="`basename "$VIRES_SERVER_HOME"`"
INSTROOT="`dirname "$VIRES_SERVER_HOME"`"
TEMPLATES_DIR_SRC="${TEMPLATES_DIR_SRC:-$CONTRIB_DIR/templates}"
TEMPLATES_DIR_DST="${INSTROOT}/${INSTANCE}/${INSTANCE}/templates"

cp -r "$TEMPLATES_DIR_SRC/." "$TEMPLATES_DIR_DST"
chown -vr "$VIRES_USER:$VIRES_GROUP" "$TEMPLATES_DIR_DST"
