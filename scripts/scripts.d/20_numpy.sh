#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: numpy installation.
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

info "Installing numpy ..."

activate_virtualenv

pip install $PIP_OPTIONS 'numpy>=1.14.0,<1.15a0'
