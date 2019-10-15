#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: VirES Jupyter Hub integration - development mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python3_venv.sh

info "Installing VirES Jupyter Hub Integration in the development mode ..."

export P3_VENV_ROOT="$VIRES_ROOT/python3_jhub"
activate_venv

pip install -e "${JHUB_SOURCE_PATH:-/usr/local/vires/vires_jhub}"