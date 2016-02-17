#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: SpacePy package installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing SpacePy package and its dependencies ..."

# install the package and its dependencies
yum --assumeyes install pytho-spacepy

