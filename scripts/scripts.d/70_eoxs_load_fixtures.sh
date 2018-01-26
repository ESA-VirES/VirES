#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Load fixtures to the EOxServer instance.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH


. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

info "Loading available EOxServer fixtures ... "

activate_virtualenv

[ -z "$CONTRIB_DIR" ] && error "Missing the required CONTRIB_DIR variable!"
[ -z "$VIRES_SERVER_HOME" ] && error "Missing the required VIRES_SERVER_HOME variable!"
[ -z "$VIRES_INSTALL_USER" ] && error "Missing the required VIRES_INSTALL_USER variable!"
[ -z "$VIRES_INSTALL_GROUP" ] && error "Missing the required VIRES_INSTALL_GROUP variable!"

INSTANCE="`basename "$VIRES_SERVER_HOME"`"
INSTROOT="`dirname "$VIRES_SERVER_HOME"`"
FIXTURES_DIR_SRC="${FIXTURES_DIR_SRC:-$CONTRIB_DIR/fixtures}"
FIXTURES_DIR_DST="${INSTROOT}/${INSTANCE}/${INSTANCE}/data/fixtures"
MNGCMD="${INSTROOT}/${INSTANCE}/manage.py"

info "loading fixtures from $FIXTURES_DIR_SRC"

{ ls "$FIXTURES_DIR_SRC/"*.json 2>/dev/null || true ; } | while read SRC_FILE
do
    FIXTURE_NAME="`basename "$SRC_FILE" .json`"
    info "Loading fixture '$FIXTURE_NAME' ..."
    DST_FILE="${FIXTURES_DIR_DST}/${FIXTURE_NAME}.json"
    cp "$SRC_FILE" "$DST_FILE"
    chown "$VIRES_INSTALL_USER:$VIRES_INSTALL_GROUP" "$DST_FILE"
    python "$MNGCMD" loaddata "$FIXTURE_NAME"
done
