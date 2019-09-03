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

activate_venv

pip install $PIP_OPTIONS pip
