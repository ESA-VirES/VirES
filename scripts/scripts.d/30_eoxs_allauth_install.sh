#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOxServer django-allauth wrapper installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Installing EOxServer django-allauth integration package from sources ..."

activate_venv "$EOXS_VENV_ROOT"

pip install $PIP_OPTIONS "${EOXS_ALLAUTH_SOURCE_PATH:-/usr/local/vires/eoxs_allauth}"
