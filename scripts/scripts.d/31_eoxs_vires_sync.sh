#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: VirES for Swarm synchronization installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2022 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh


if [ -n "$VIRES_SYNC_SOURCE_PATH" -a -d "$VIRES_SYNC_SOURCE_PATH" ]
then
    info "Installing VirES for Swarm product synchronization from source ..."

    activate_venv "$VIRES_VENV_ROOT"

    pip install "$VIRES_SYNC_SOURCE_PATH"
else
    warn "Installation of VirES for Swarm product synchronization skipped."
fi
