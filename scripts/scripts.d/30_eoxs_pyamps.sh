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

# pyAMPS fails with dask>2.17.0
# GDAL requires setuptools<58
#pip install $PIP_OPTIONS -r https://raw.githubusercontent.com/klaundal/pyAMPS/master/requirements.txt
pip install $PIP_OPTIONS -r /dev/stdin <<END
setuptools>=30.3.0,<58
future>=0.16
numpy>=1.14
matplotlib
scipy>=0.9
toolz>=0.8
pandas>=0.20
dask<2.17.0
apexpy>=1.0
END
# installing pyAMPS directly from the Git repo
pip install $PIP_OPTIONS git+https://github.com/klaundal/pyAMPS.git@v.1.5.2#pyamps
