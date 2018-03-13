#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: SpacePy package installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

info "Installing SpacePy package and its dependencies ..."

activate_virtualenv

yum --assumeyes install cdf

pip install $PIP_OPTIONS SpacePy
