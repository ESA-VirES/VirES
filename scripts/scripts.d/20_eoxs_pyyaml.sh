#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: pyyaml installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2022 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Installing pyyaml ..."

activate_venv "$VIRES_VENV_ROOT"

pip install $PIP_OPTIONS 'pyyaml'
