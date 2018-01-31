#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOxServer django-allauth warpper installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

info "Installing EOxServer django-allauth integration package from sources ..."

activate_virtualenv

pip install $PIP_OPTIONS --force-reinstall "${EOXS_ALLAUTH_SOURCE_PATH:-/usr/local/vires/eoxs_allauth}"
