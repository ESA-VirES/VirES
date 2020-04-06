#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOxServer WPS asynchronous back-end installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Installing EOxServer asynchronous WPS backend in development mode."

activate_venv "$VIRES_VENV_ROOT"

pip install -e "${EOXS_WPS_ASYNC_SOURCE_PATH:-/usr/local/eoxs_wps_async}"
