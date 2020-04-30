#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: pyAPMS installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Installing pyAMPS ..."

activate_venv "$VIRES_VENV_ROOT"

#pip install $PIP_OPTIONS pyamps
# installing 1.4.1-rc directly from the Git repo
pip install $PIP_OPTIONS -r https://raw.githubusercontent.com/klaundal/pyAMPS/master/requirements.txt
pip install $PIP_OPTIONS git+https://github.com/klaundal/pyAMPS.git@0661c5d6faba0f0f0be567118ab4b0307e462d5e#pyamps
