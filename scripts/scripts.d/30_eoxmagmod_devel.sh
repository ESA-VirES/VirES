#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOX magnetic model library installation - development mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

info "Installing EOxMagMod in development mode ..."

activate_virtualenv

yum --assumeyes install wmm2015-lib qdipole wmm2015-devel qdipole-devel

pip install -e "${EOXMAGMOD_SOURCE_PATH:-/usr/local/eoxmagmod}"
