#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: VirES OAuth2 server installation - development mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Installing VirES for Swarm server packages from sources ..."

activate_venv "$OAUTH_VENV_ROOT"

pip install $PIP_OPTIONS "${OAUTH_SOURCE_PATH:-/usr/local/vires/vires_oauth}"
