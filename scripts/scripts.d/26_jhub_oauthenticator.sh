#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Jupyter Hub installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python3_venv.sh

info "Installing Jupyter Hub OAuth2 Autheticator ..."

export P3_VENV_ROOT="$VIRES_ROOT/python3_jhub"
activate_venv

pip install $PIP_OPTIONS oauthenticator
