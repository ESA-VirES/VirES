#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: scipy installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Installing scipy ..."

activate_venv "$EOXS_VENV_ROOT"

pip install $PIP_OPTIONS 'scipy>=1.4.0,<1.5a0'
