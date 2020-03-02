#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: django-allauth installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Installing django-allauth ..."

activate_venv "$OAUTH_VENV_ROOT"

pip install $PIP_OPTIONS django-allauth
pip install $PIP_OPTIONS django-countries