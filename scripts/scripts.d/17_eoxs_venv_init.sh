#!/bin/sh
#-------------------------------------------------------------------------------
#
# VirES-Server venv initialization
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Initializing VirES-Server Python venv ..."

export VENV_ROOT="$VIRES_VENV_ROOT"
is_venv_enabled && create_venv_root_if_missing
activate_venv

pip install $PIP_OPTIONS pip
