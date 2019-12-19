#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: pyAPMS installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

info "Installing pyAMPS from PyPI"

activate_virtualenv

pip install $PIP_OPTIONS pyamps
