#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: django-requestlogging installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2016 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

info "Installing django-requestlogging ..."

activate_virtualenv

pip install $PIP_OPTIONS django-requestlogging
