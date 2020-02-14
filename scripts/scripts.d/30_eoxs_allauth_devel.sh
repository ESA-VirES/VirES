#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOxServer django-allauth wrapper installation - development mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Installing EOxServer django-allauth integration package in the development mode ..."

activate_venv "$EOXS_VENV_ROOT"

pip install -e "${EOXS_ALLAUTH_SOURCE_PATH:-/usr/local/vires/eoxs_allauth/}"
