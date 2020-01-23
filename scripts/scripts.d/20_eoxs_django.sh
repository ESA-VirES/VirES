#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Django installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Installing Django ..."

activate_venv "$EOXS_VENV_ROOT"

pip install $PIP_OPTIONS 'Django>=2.2.2,<3.0'
pip install $PIP_OPTIONS django-requestlogging
