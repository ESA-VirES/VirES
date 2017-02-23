#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOX server installation - development mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing EOxServer in the development mode."

# Path to the EOxServer development directory tree:
EOXS_DEV_PATH="${EOXS_DEV_PATH:-/usr/local/eoxserver}"


# STEP 1: INSTALL DEPENDENCIES
yum --assumeyes install python-dateutil python-lxml proj-epsg python-setuptools

# STEP 2: INSTALL EOXSERVER
# Install EOxServer in the development mode.
PACKAGE=EOxServer
[ -z "`pip freeze | grep "$PACKAGE==" `" ] || pip uninstall -y "$PACKAGE"
pushd .
cd $EOXS_DEV_PATH
[ ! -d build/ ] || rm -fvR build/
[ ! -d dist/ ] || rm -fvR dist/
python ./setup.py install
popd
