#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: django-simple-captcha installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2020 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Installing Django Simple Captcha ..."

activate_venv "$OAUTH_VENV_ROOT"

pip install $PIP_OPTIONS django-simple-captcha
