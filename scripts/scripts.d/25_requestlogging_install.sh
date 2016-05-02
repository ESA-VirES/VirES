#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: django-requestlogging installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2016 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing django-requestlogging ..."

pip install --upgrade --no-deps django-requestlogging
