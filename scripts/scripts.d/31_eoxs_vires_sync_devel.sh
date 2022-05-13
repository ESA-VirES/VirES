#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: VirES for Swarm synchronization - development mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2022 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

VIRES_SYNC_SOURCE_PATH=${VIRES_SYNC_SOURCE_PATH:-/usr/local/vires_sync}

if [ -d "$VIRES_SYNC_SOURCE_PATH" ]
then
    info "Installing VirES for Swarm product synchronization in the development mode ..."

    activate_venv "$VIRES_VENV_ROOT"

    pip install -e "$VIRES_SYNC_SOURCE_PATH"
else
    warn "Installation of VirES for Swarm product synchronization skipped."
fi
