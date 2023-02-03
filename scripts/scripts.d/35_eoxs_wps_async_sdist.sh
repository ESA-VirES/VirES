#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOxServer WPS asynchronous back-end installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

#TODO: fix the backend version
SOURCE_URL="https://github.com/DAMATS/WPS-Backend/archive/0.5.4.tar.gz"

info "Installing EOxServer asynchronous WPS backend."

activate_venv "$VIRES_VENV_ROOT"

pip install $PIP_OPTIONS "$SOURCE_URL"
