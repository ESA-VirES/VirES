#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Jupyter Hub installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python3_venv.sh

info "Installing Jupyter Hub ..."

export P3_VENV_ROOT="$VIRES_ROOT/python3_jhub"
activate_venv

pip install $PIP_OPTIONS jupyterhub
npm install -g configurable-http-proxy
pip install $PIP_OPTIONS notebook
pip install $PIP_OPTIONS jupyterlab
