#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Load fixtures to the EOxServer instance.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH


. `dirname $0`/../lib_logging.sh

info "Loading available EOxServer fixtures ... "

[ -z "$CONTRIB_DIR" ] && error "Missing the required CONTRIB_DIR variable!"
[ -z "$VIRES_SERVER_HOME" ] && error "Missing the required VIRES_SERVER_HOME variable!"
[ -z "$VIRES_USER" ] && error "Missing the required VIRES_USER variable!"
[ -z "$VIRES_GROUP" ] && error "Missing the required VIRES_GROUP variable!"

INSTANCE="`basename "$VIRES_SERVER_HOME"`"
INSTROOT="`dirname "$VIRES_SERVER_HOME"`"
FIXTURES_DIR_SRC="${FIXTURES_DIR_SRC:-$CONTRIB_DIR/fixtures}"
FIXTURES_DIR_DST="${INSTROOT}/${INSTANCE}/${INSTANCE}/data/fixtures"
MNGCMD="${INSTROOT}/${INSTANCE}/manage.py"

{ ls "$FIXTURES_DIR_SRC/"*.json 2>/dev/null || true ; } | while read SRC
do
    FNAME="`basename "$SRC" .json`"
    info "Loading fixture '$FNAME' ..."
    DST="${FIXTURES_DIR_DST}/${FNAME}.json"
    cp "$SRC" "$DST"
    chown -v "$VIRES_USER:$VIRES_GROUP" "$DST"
    sudo -u "$VIRES_USER" python "$MNGCMD" loaddata "$FNAME"
done
