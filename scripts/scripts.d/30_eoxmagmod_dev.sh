#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: EOX magnetic model library - development mode
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Installing EOxServer in the development mode."

# Path to the EOxServer development directory tree:
EOXMM_DEV_PATH="${EOXMM_DEV_PATH:-/usr/local/eoxmagmod}"

# STEP 1: INSTALL DEPENDENCIES
yum --assumeyes install gcc-gfortran

# STEP 2: INSTALL EOXMM
# Install EOxServer in the development mode.
pushd .
cd $EOXMM_DEV_PATH
# build dependencies
pushd .
cd eoxmagmod/geomaglib
make clean build install
popd
pushd .
cd eoxmagmod/qdipolelib
make clean build install
popd
# install python package
python ./setup.py develop
popd
