#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOX magnetic model library installation - development mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_virtualenv.sh

EOXMAGMOD_SOURCE_PATH="${EOXMAGMOD_SOURCE_PATH:-/usr/local/eoxmagmod}"

info "Installing EOxMagMod in development mode ..."

activate_virtualenv

yum --assumeyes install wmm2015-lib qdipole wmm2015-devel qdipole-devel

# get rid of the previous build
[ -d "$EOXMAGMOD_SOURCE_PATH/build" ] && rm -fvR "$EOXMAGMOD_SOURCE_PATH/build"
[ -d "$EOXMAGMOD_SOURCE_PATH/dist" ] && rm -fvR "$EOXMAGMOD_SOURCE_PATH/dist"
pip install -e "$EOXMAGMOD_SOURCE_PATH"
