#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Django installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Installing Django OAuth Toolkit ..."

activate_venv "$OAUTH_VENV_ROOT"

pip install $PIP_OPTIONS django-oauth-toolkit==1.7.0 # FIXME implement proper support for django-oauth-toolkit >= 2.0.0
