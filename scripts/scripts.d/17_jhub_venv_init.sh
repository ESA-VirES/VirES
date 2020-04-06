#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: JupyterHub venv initialization
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Initializing JupyterHub Python venv ..."

export VENV_ROOT="$JHUB_VENV_ROOT"
is_venv_enabled && create_venv_root_if_missing
activate_venv

pip install $PIP_OPTIONS pip
