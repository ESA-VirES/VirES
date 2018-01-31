#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOxServer django-allauth warpper installation - development mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

info "Installing EOxServer django-allauth integration package in the development mode ..."

activate_virtualenv

pip install -e "${EOXS_ALLAUTH_SOURCE_PATH:-/usr/local/vires/eoxs_allauth/}"
