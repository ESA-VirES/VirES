#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: PIP Python package mamager upgrade
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python3_venv.sh

info "Upgrading PIP Python package manager ..."

export P3_VENV_ROOT="$VIRES_ROOT/python3_jhub"
[ -d "$P3_VENV_ROOT" ] || {
    sudo -u root mkdir -m 0755 -p "$P3_VENV_ROOT"
}
activate_venv

pip install $PIP_OPTIONS pip
