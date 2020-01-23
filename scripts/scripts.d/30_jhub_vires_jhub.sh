#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: VirES Jupyter Hub integration - development mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Installing VirES Jupyter Hub Integration in the development mode ..."

activate_venv "$JHUB_VENV_ROOT"

JHUB_SOURCE_PATH="${JHUB_SOURCE_PATH:-/usr/local/vires/vires_jhub}"

pip install -e "$JHUB_SOURCE_PATH"

# link VirES custom static assets
ln -sf "$JHUB_SOURCE_PATH/share/vires_jhub/static" "${JHUB_VENV_ROOT}/share/jupyterhub/static/vires"
