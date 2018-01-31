#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: VirES for Swarm server installation - development mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

info "Installing VirES for Swarm server packages in the development mode ..."

activate_virtualenv

pip install -e "${VIRES_SOURCE_PATH:-/usr/local/vires/vires}"
