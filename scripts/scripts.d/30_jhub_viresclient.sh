#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: VirES JHub - VirES Python client installation 
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Installing VirES Python client in the development mode ..."

activate_venv "$JHUB_VENV_ROOT"

JHUB_SOURCE_PATH="${JHUB_SOURCE_PATH:-/usr/local/viresclient}"

pip install -e "$JHUB_SOURCE_PATH"
