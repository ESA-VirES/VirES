#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Load fixtures to the EOxServer instance.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh
. `dirname $0`/../lib_eoxserver.sh

info "Loading available EOxServer fixtures ... "

activate_virtualenv

set_instance_variables

required_variables CONTRIB_DIR VIRES_INSTALL_USER VIRES_INSTALL_GROUP
required_variables FIXTURES_DIR MNGCMD

FIXTURES_DIR_SRC="${FIXTURES_DIR_SRC:-$CONTRIB_DIR/fixtures}"

info "Loading fixtures from $FIXTURES_DIR_SRC"

{ ls "$FIXTURES_DIR_SRC/"*.json 2>/dev/null || true ; } | while read SRC_FILE
do
    FIXTURE_NAME="`basename "$SRC_FILE" .json`"
    info "Loading fixture '$FIXTURE_NAME' ..."
    DST_FILE="${FIXTURES_DIR}/${FIXTURE_NAME}.json"
    cp "$SRC_FILE" "$DST_FILE"
    [ -n "$VIRES_ENVIRONMENT" ] && sed -e 's|<environment>|%s|g' -i "$DST_FILE"
    chown "$VIRES_INSTALL_USER:$VIRES_INSTALL_GROUP" "$DST_FILE"
    python "$MNGCMD" loaddata "$FIXTURE_NAME"
done
