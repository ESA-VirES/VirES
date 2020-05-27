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
# pyAMPS fails with dask-2.17.0
#pip install $PIP_OPTIONS -r https://raw.githubusercontent.com/klaundal/pyAMPS/master/requirements.txt
pip install $PIP_OPTIONS -r /dev/stdin <<END
setuptools>=30.3.0
future>=0.16
numpy>=1.14
matplotlib
scipy>=0.9
toolz>=0.8
pandas>=0.20
dask<2.17.0
apexpy>=1.0
END
pip install $PIP_OPTIONS git+https://github.com/klaundal/pyAMPS.git@0661c5d6faba0f0f0be567118ab4b0307e462d5e#pyamps
