#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOX server installation - development mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Installing EOxServer from sources ..."

activate_venv "$EOXS_VENV_ROOT"

pip install $PIP_OPTIONS lxml
pip install $PIP_OPTIONS "${EOXSERVER_SOURCE_PATH:-/usr/local/eoxserver}"
